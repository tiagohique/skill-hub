import io
import stat
import zipfile

import pytest

from hub.domain.errors import LimitExceededError, SkillValidationError
from hub.service.validation import UploadLimits, parse_upload

LIMITS = UploadLimits(max_file_bytes=1024 * 1024, max_bundle_bytes=5 * 1024 * 1024, max_files=100)
GOOD = "---\nname: my-skill\ndescription: Faz algo útil\n---\n# Corpo\n"


def make_zip(files: dict[str, bytes | str], *, symlinks: tuple[str, ...] = ()) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            info = zipfile.ZipInfo(name)
            if name in symlinks:
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(info, content)
    return buf.getvalue()


def test_valid_md() -> None:
    parsed = parse_upload("SKILL.md", GOOD.encode(), "1.0.0", LIMITS)
    assert parsed.name == "my-skill"
    assert parsed.description == "Faz algo útil"
    assert [f.path for f in parsed.files] == ["SKILL.md"]
    assert parsed.files[0].data == GOOD.encode()


def test_md_filename_is_case_insensitive_and_any_name() -> None:
    parsed = parse_upload("minha-skill.MD", GOOD.encode(), "1.0.0", LIMITS)
    assert parsed.files[0].path == "SKILL.md"


def test_zip_at_root() -> None:
    data = make_zip({"SKILL.md": GOOD, "ref/a.md": "x"})
    parsed = parse_upload("s.zip", data, "1.0.0", LIMITS)
    assert sorted(f.path for f in parsed.files) == ["SKILL.md", "ref/a.md"]


def test_zip_with_single_top_folder_strips_prefix() -> None:
    data = make_zip({"my-skill/SKILL.md": GOOD, "my-skill/ref/a.md": "x"})
    parsed = parse_upload("s.zip", data, "1.0.0", LIMITS)
    assert sorted(f.path for f in parsed.files) == ["SKILL.md", "ref/a.md"]


def test_zip_from_finder_ignores_macosx_and_ds_store() -> None:
    data = make_zip(
        {
            "my-skill/SKILL.md": GOOD,
            "my-skill/.DS_Store": "junk",
            "__MACOSX/my-skill/._SKILL.md": "junk",
            "__MACOSX/._my-skill": "junk",
        }
    )
    parsed = parse_upload("s.zip", data, "1.0.0", LIMITS)
    assert [f.path for f in parsed.files] == ["SKILL.md"]


def test_zip_without_skill_md() -> None:
    with pytest.raises(SkillValidationError, match="SKILL.md"):
        parse_upload("s.zip", make_zip({"README.md": "x"}), "1.0.0", LIMITS)


@pytest.mark.parametrize("bad", ["../evil.md", "a/../../evil.md", "/abs.md", "a\\b.md"])
def test_zip_rejects_dangerous_paths(bad: str) -> None:
    data = make_zip({"SKILL.md": GOOD, bad: "x"})
    with pytest.raises(SkillValidationError):
        parse_upload("s.zip", data, "1.0.0", LIMITS)


def test_zip_rejects_symlink() -> None:
    data = make_zip({"SKILL.md": GOOD, "link": "/etc/passwd"}, symlinks=("link",))
    with pytest.raises(SkillValidationError, match="link"):
        parse_upload("s.zip", data, "1.0.0", LIMITS)


def test_zip_rejects_duplicate_names() -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("SKILL.md", GOOD)
        with pytest.warns(UserWarning):
            zf.writestr("SKILL.md", GOOD)
    with pytest.raises(SkillValidationError, match="duplicad"):
        parse_upload("s.zip", buf.getvalue(), "1.0.0", LIMITS)


def test_zip_rejects_file_outside_skill_folder() -> None:
    data = make_zip({"my-skill/SKILL.md": GOOD, "other/x.md": "x"})
    with pytest.raises(SkillValidationError, match="fora"):
        parse_upload("s.zip", data, "1.0.0", LIMITS)


def test_invalid_zip_bytes() -> None:
    with pytest.raises(SkillValidationError, match="zip"):
        parse_upload("s.zip", b"not a zip", "1.0.0", LIMITS)


def test_too_many_files() -> None:
    files: dict[str, bytes | str] = {"SKILL.md": GOOD}
    files.update({f"f{i}.txt": "x" for i in range(100)})
    with pytest.raises(LimitExceededError):
        parse_upload("s.zip", make_zip(files), "1.0.0", LIMITS)


def test_file_over_limit_uses_real_size_not_declared() -> None:
    small = UploadLimits(max_file_bytes=1024, max_bundle_bytes=10**6, max_files=10)
    data = make_zip({"SKILL.md": GOOD, "big.bin": b"\0" * 2_000_000})
    with pytest.raises(LimitExceededError):
        parse_upload("s.zip", data, "1.0.0", small)


def test_forged_declared_size_is_not_trusted() -> None:
    small = UploadLimits(max_file_bytes=1024, max_bundle_bytes=10**6, max_files=10)
    data = bytearray(make_zip({"SKILL.md": GOOD, "big.bin": b"\0" * 5000}))
    # Falsifica file_size declarado (cabeçalho central e local) para 10 bytes.
    real = (5000).to_bytes(4, "little")
    fake = (10).to_bytes(4, "little")
    pos = 0
    while (pos := data.find(real, pos)) != -1:
        data[pos : pos + 4] = fake
        pos += 4
    with pytest.raises((LimitExceededError, SkillValidationError)):
        parse_upload("s.zip", bytes(data), "1.0.0", small)


def test_bundle_over_limit() -> None:
    small = UploadLimits(max_file_bytes=10**6, max_bundle_bytes=3000, max_files=10)
    data = make_zip({"SKILL.md": GOOD, "a.bin": b"a" * 2000, "b.bin": b"b" * 2000})
    with pytest.raises(LimitExceededError):
        parse_upload("s.zip", data, "1.0.0", small)


def test_md_over_file_limit() -> None:
    small = UploadLimits(max_file_bytes=10, max_bundle_bytes=10**6, max_files=10)
    with pytest.raises(LimitExceededError):
        parse_upload("SKILL.md", GOOD.encode(), "1.0.0", small)


def test_bom_and_crlf_accepted_and_bytes_preserved() -> None:
    raw = b"\xef\xbb\xbf" + GOOD.replace("\n", "\r\n").encode()
    parsed = parse_upload("SKILL.md", raw, "1.0.0", LIMITS)
    assert parsed.name == "my-skill"
    assert parsed.files[0].data == raw


@pytest.mark.parametrize(
    "text",
    [
        "# sem frontmatter\n",
        "---\nname: a\ndescription: b\n# sem fechamento\n",
        "---\n- a\n- b\n---\n",
        "---\nname: [oops\n---\n",
        "---\ndescription: sem nome\n---\n",
        "---\nname: a\n---\n",
        "---\nname: a\ndescription: ''\n---\n",
        "---\nname: My_Skill\ndescription: x\n---\n",
        "---\nname: -a\ndescription: x\n---\n",
        "---\nname: a--b\ndescription: x\n---\n",
    ],
)
def test_invalid_frontmatter(text: str) -> None:
    with pytest.raises(SkillValidationError):
        parse_upload("SKILL.md", text.encode(), "1.0.0", LIMITS)


def test_non_utf8_skill_md() -> None:
    with pytest.raises(SkillValidationError, match="UTF-8"):
        parse_upload("SKILL.md", b"---\nname: a\n\xff\n---\n", "1.0.0", LIMITS)


def test_metadata_version_must_match() -> None:
    ok = "---\nname: a\ndescription: x\nmetadata:\n  version: '1.0.0'\n---\n"
    assert parse_upload("SKILL.md", ok.encode(), "1.0.0", LIMITS).name == "a"
    with pytest.raises(SkillValidationError, match="versão"):
        parse_upload("SKILL.md", ok.encode(), "2.0.0", LIMITS)


def test_metadata_version_float_does_not_match_semver() -> None:
    text = "---\nname: a\ndescription: x\nmetadata:\n  version: 1.0\n---\n"
    with pytest.raises(SkillValidationError, match="versão"):
        parse_upload("SKILL.md", text.encode(), "1.0.0", LIMITS)


@pytest.mark.parametrize("version", ["1.0", "v1.0.0", "", "1.0.0.0"])
def test_invalid_semver(version: str) -> None:
    with pytest.raises(SkillValidationError, match="semver"):
        parse_upload("SKILL.md", GOOD.encode(), version, LIMITS)


def test_unsupported_extension() -> None:
    with pytest.raises(SkillValidationError, match=r"\.md"):
        parse_upload("skill.txt", GOOD.encode(), "1.0.0", LIMITS)


def test_yaml_aliases_rejected() -> None:
    text = "---\nname: a\ndescription: &x hello\nother: *x\n---\n"
    with pytest.raises(SkillValidationError, match="alias"):
        parse_upload("SKILL.md", text.encode(), "1.0.0", LIMITS)


def test_yaml_dates_become_json_safe() -> None:
    text = "---\nname: a\ndescription: x\ncreated: 2024-01-31\n---\n"
    parsed = parse_upload("SKILL.md", text.encode(), "1.0.0", LIMITS)
    assert parsed.frontmatter["created"] == "2024-01-31"
