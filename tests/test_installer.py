import platform
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from installer import install_bookkeeppr


@pytest.mark.parametrize(
    "mock_os, mock_env_var, expected_target",
    [
        ("Windows", "C:/MockAppData", Path("C:/MockAppData") / "Bookkeeppr"),
        ("Darwin", None, Path("/Applications/Bookkeeppr")),
        ("Linux", None, Path.home() / ".local" / "bin" / "Bookkeeppr"),
    ],
)
@patch("shutil.copy2")
@patch("shutil.copytree")
def test_install_bookkeeppr_creates_target_directory(
    mock_copytree,
    mock_copy2,
    mock_os,
    mock_env_var,
    expected_target,
    capsys,
):
    with (
        patch("platform.system", return_value=mock_os),
        patch("os.getenv", return_value=mock_env_var),
    ):

        # Create a fake temp directory structure as the source
        with tempfile.TemporaryDirectory() as temp_root:
            temp_root_path = Path(temp_root)

            # Create fake files and folders representing app files
            (temp_root_path / "app.py").write_text("# app entry")
            lib_dir = temp_root_path / "lib"
            lib_dir.mkdir(parents=True, exist_ok=True)
            (lib_dir / "__init__.py").touch()
            (lib_dir / "__init__.py").write_text("# init")
            (temp_root_path / "tests").mkdir()
            (temp_root_path / "tests" / "__init__.py").write_text(
                "# test init"
            )

            with (
                patch(
                    "installer.__file__", str(temp_root_path / "installer.py")
                ),
                patch("pathlib.Path.mkdir") as mock_mkdir,
            ):
                install_bookkeeppr()

                # Assert install directory creation
                mock_mkdir.assert_called_with(parents=True, exist_ok=True)

                # Assert app files were copied (not test files)
                copied_files = [
                    call.args[0].name for call in mock_copy2.call_args_list
                ]
                assert "app.py" in copied_files
                assert "lib" in [
                    call.args[0].name for call in mock_copytree.call_args_list
                ]
                assert "tests" not in copied_files

                captured = capsys.readouterr()
                assert (
                    f"[INSTALL] Installing to: {expected_target}"
                    in captured.out
                )
