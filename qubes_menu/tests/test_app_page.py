# -*- encoding: utf8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2023 Marta Marczykowska-Górecka
#                               <marmarta@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>.
from unittest import mock

from ..desktop_file_manager import DesktopFileManager
from ..vm_manager import VMManager
from ..custom_widgets import FolderRow, SelfAwareMenu
from .. import constants
from qubesadmin.tests.mock_app import MockDispatcher, MockQube
from ..application_page import AppPage
from ..settings_page import SettingsPage


def test_app_page_vm_state(test_desktop_file_path, test_qapp, test_builder):
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)

    # For some reason it defaults to the system tab.
    app_page.toggle_buttons.apps_toggle.set_active(True)

    # select dom0
    app_page.vm_list.select_row(
        [
            row
            for row in app_page.vm_list.get_children()
            if row.vm_name == "dom0"
        ][0]
    )
    assert app_page.control_list.start_item.row_label.get_label() == " "
    assert app_page.control_list.pause_item.row_label.get_label() == " "

    # select a turned off vm
    app_page.vm_list.select_row(
        [
            row
            for row in app_page.vm_list.get_children()
            if row.vm_name == "test-red"
        ][0]
    )

    assert (
        app_page.control_list.start_item.row_label.get_label() == "Start qube"
    )
    assert app_page.control_list.pause_item.row_label.get_label() == " "

    # select a turned on vm
    app_page.vm_list.select_row(
        [
            row
            for row in app_page.vm_list.get_children()
            if row.vm_name == "sys-usb"
        ][0]
    )

    assert (
        app_page.control_list.start_item.row_label.get_label()
        == "Shutdown qube"
    )
    assert (
        app_page.control_list.pause_item.row_label.get_label() == "Pause qube"
    )

    # select a turned off disposable template
    app_page.vm_list.select_row(
        [
            row
            for row in app_page.vm_list.get_children()
            if row.vm_name == "test-alt-dvm"
        ][0]
    )
    assert app_page.control_list.start_item.row_label.get_label() == " "
    assert app_page.control_list.pause_item.row_label.get_label() == " "

    # select a turned on disposable template
    app_page.vm_list.select_row(
        [
            row
            for row in app_page.vm_list.get_children()
            if row.vm_name == "test-alt-dvm-running"
        ][0]
    )
    assert (
        app_page.control_list.start_item.row_label.get_label()
        == "Shutdown qube"
    )
    assert (
        app_page.control_list.pause_item.row_label.get_label() == "Pause qube"
    )


def test_dispvm_parent_sorting(test_desktop_file_path, test_qapp, test_builder):
    # check if dispvm child is sorted after the parent
    test_qapp._qubes["disp1233"] = MockQube(
        name="disp1233",
        qapp=test_qapp,
        klass="DispVM",
        template_for_dispvms="True",
        template="default-dvm",
        auto_cleanup=True,
    )
    test_qapp.update_vm_calls()

    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)

    found_dvm = False

    for row in app_page.vm_list.get_children():
        if found_dvm:
            if row.vm_name == "disp1233" and row.vm_entry.parent_vm:
                break
            found_dvm = False
            continue
        if row.vm_entry.is_dispvm_template:
            found_dvm = True
            continue
        found_dvm = False
    else:
        assert False


def test_settings_app_page(test_desktop_file_path, test_qapp, test_builder):
    # a basic sanity test
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    settings_page = SettingsPage(
        test_qapp, test_builder, desktop_file_manager, dispatcher
    )

    for row in settings_page.app_list.get_children():
        assert not row.app_info.vm


def test_folder_create_assign_rename_delete(
    test_desktop_file_path, test_qapp, test_builder
):
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    app_page.toggle_buttons.apps_toggle.set_active(True)
    app_page._save_folder_state = mock.Mock()

    vm_entry = vm_manager.load_vm_from_name("test-red")
    assert vm_entry
    vm_entry.vm.features = {}

    app_page._assign_folder(vm_entry, "Work")
    assert "Work" in app_page.folder_order
    assert app_page._vm_folder(vm_entry) == "Work"
    assert vm_entry.vm.features[constants.FOLDER_FEATURE] == "Work"

    app_page._rename_folder("Work", "Projects")
    assert "Work" not in app_page.folder_order
    assert "Projects" in app_page.folder_order
    assert app_page._vm_folder(vm_entry) == "Projects"
    assert vm_entry.vm.features[constants.FOLDER_FEATURE] == "Projects"

    app_page._delete_folder("Projects")
    assert "Projects" not in app_page.folder_order
    assert app_page._vm_folder(vm_entry) == ""
    assert constants.FOLDER_FEATURE not in vm_entry.vm.features


def test_folder_move_and_collapsed_state_saved(
    test_desktop_file_path, test_qapp, test_builder
):
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    app_page.toggle_buttons.apps_toggle.set_active(True)

    # The mock app cannot observe feature writes made through the dom0
    # qubesadmin wrapper (they raise and are swallowed); mirror saves into
    # the mock feature store instead, like other tests do with update_calls.
    dom0_mock = test_qapp._qubes["dom0"]

    def fake_save():
        dom0_mock.features[constants.FOLDER_ORDER_FEATURE] = " ".join(
            app_page.folder_order
        )
        dom0_mock.features[constants.FOLDER_COLLAPSED_FEATURE] = " ".join(
            sorted(app_page.collapsed_folders)
        )
        dom0_mock.update_calls()

    app_page._save_folder_state = fake_save

    for name, folder in zip(
        ["test-red", "sys-usb", "test-vm"], ["A", "B", "C"]
    ):
        vm_entry = vm_manager.load_vm_from_name(name)
        assert vm_entry
        vm_entry.vm.features = {}
        app_page._assign_folder(vm_entry, folder)

    assert app_page.folder_order == [app_page.UNGROUPED, "A", "B", "C"]
    assert (
        dom0_mock.features[constants.FOLDER_ORDER_FEATURE] == "Ungrouped A B C"
    )

    app_page._move_folder(None, "B", -1)
    assert app_page.folder_order == [app_page.UNGROUPED, "B", "A", "C"]
    assert (
        dom0_mock.features[constants.FOLDER_ORDER_FEATURE] == "Ungrouped B A C"
    )

    app_page._move_folder(None, "B", 1)
    assert app_page.folder_order == [app_page.UNGROUPED, "A", "B", "C"]

    folder_b = app_page.folder_rows["B"]
    assert isinstance(folder_b, FolderRow)
    assert "B" not in app_page.collapsed_folders

    app_page._toggle_folder(folder_b)
    assert "B" in app_page.collapsed_folders
    assert dom0_mock.features[constants.FOLDER_COLLAPSED_FEATURE] == "B"

    app_page._set_all_folders_collapsed(None, True)
    assert set(app_page.folder_order) == app_page.collapsed_folders

    app_page._set_all_folders_collapsed(None, False)
    assert app_page.collapsed_folders == set()


def test_folder_reordering_is_not_pinned_to_ungrouped(
    test_desktop_file_path, test_qapp, test_builder
):
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    app_page.toggle_buttons.apps_toggle.set_active(True)

    dom0_mock = test_qapp._qubes["dom0"]

    def fake_save():
        dom0_mock.features[constants.FOLDER_ORDER_FEATURE] = " ".join(
            app_page.folder_order
        )
        dom0_mock.features[constants.FOLDER_COLLAPSED_FEATURE] = " ".join(
            sorted(app_page.collapsed_folders)
        )
        dom0_mock.update_calls()

    app_page._save_folder_state = fake_save

    for name, folder in zip(
        ["test-red", "sys-usb", "test-vm"], ["A", "B", "C"]
    ):
        vm_entry = vm_manager.load_vm_from_name(name)
        assert vm_entry
        vm_entry.vm.features = {}
        app_page._assign_folder(vm_entry, folder)

    assert app_page.folder_order == [app_page.UNGROUPED, "A", "B", "C"]

    def expect_swap(folder_order, name, direction):
        """Order the move is expected to produce: a swap with the nearest
        *visible* neighbor (folders hidden in this tab are skipped and
        left unchanged)."""
        other = app_page._visible_adjacent_folder(name, direction)
        if other is None:
            return list(folder_order)
        index = folder_order.index(name)
        other_index = folder_order.index(other)
        swapped = list(folder_order)
        swapped[index], swapped[other_index] = (
            swapped[other_index],
            swapped[index],
        )
        return swapped

    def move_and_check(name, direction):
        expected = expect_swap(app_page.folder_order, name, direction)
        app_page._move_folder(None, name, direction)
        assert app_page.folder_order == expected
        assert dom0_mock.features[constants.FOLDER_ORDER_FEATURE] == " ".join(
            expected
        )

    # a real folder may move onto the first slot - nothing is pinned
    move_and_check("A", -1)
    assert app_page.folder_order != [app_page.UNGROUPED, "A", "B", "C"]

    # Ungrouped itself is movable in both directions and the persisted
    # order keeps its position after the reload done on each rebuild
    move_and_check(app_page.UNGROUPED, 1)
    assert app_page.folder_order[0] != app_page.UNGROUPED
    move_and_check(app_page.UNGROUPED, -1)

    # at the ends there is no visible neighbor: the move is a no-op
    move_and_check("C", 1)
    move_and_check("A", -1)


def test_folder_rebuild_is_deferred_while_popup_is_open(
    test_desktop_file_path, test_qapp, test_builder
):
    """Folder operations run from an open context menu (the popup's anchor
    row is destroyed by the rebuild) must defer the row rebuild out of the
    popup emission; state and persistence stay synchronous."""
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    app_page.toggle_buttons.apps_toggle.set_active(True)

    dom0_mock = test_qapp._qubes["dom0"]

    def fake_save():
        dom0_mock.features[constants.FOLDER_ORDER_FEATURE] = " ".join(
            app_page.folder_order
        )
        dom0_mock.features[constants.FOLDER_COLLAPSED_FEATURE] = " ".join(
            sorted(app_page.collapsed_folders)
        )
        dom0_mock.update_calls()

    app_page._save_folder_state = fake_save

    for name, folder in zip(
        ["test-red", "sys-usb", "test-vm"], ["A", "B", "C"]
    ):
        vm_entry = vm_manager.load_vm_from_name(name)
        assert vm_entry
        vm_entry.vm.features = {}
        app_page._assign_folder(vm_entry, folder)

    assert app_page.folder_order == [app_page.UNGROUPED, "A", "B", "C"]

    # while a menu is open the rebuild is deferred to the next main loop
    # iteration instead of running inside the menu's activate emission
    with mock.patch.object(SelfAwareMenu, "OPEN_MENUS", 1):
        with mock.patch.object(app_page, "_rebuild_folder_rows") as rebuild:
            with mock.patch(
                "qubes_menu.application_page.GLib.idle_add"
            ) as idle_add:
                app_page._move_folder(None, "B", -1)
                rebuild.assert_not_called()
                idle_add.assert_called_once()

                # state and persistence are already updated synchronously
                assert app_page.folder_order == [
                    app_page.UNGROUPED,
                    "B",
                    "A",
                    "C",
                ]
                assert (
                    dom0_mock.features[constants.FOLDER_ORDER_FEATURE]
                    == "Ungrouped B A C"
                )

                # run the deferred rebuild the way the main loop would
                idle_add.call_args.args[0]()
                rebuild.assert_called_once()

    # outside of a menu the rebuild stays synchronous
    with mock.patch.object(app_page, "_rebuild_folder_rows") as rebuild:
        app_page._move_folder(None, "C", -1)
        rebuild.assert_called_once()
    assert app_page.folder_order == [
        app_page.UNGROUPED,
        "B",
        "C",
        "A",
    ]


def test_folder_state_is_global_across_tabs(
    test_desktop_file_path, test_qapp, test_builder
):
    # Folder organization is global: the same folder list and collapsed
    # state apply in every scope (Apps, Templates, Service).
    test_qapp._qubes["test-red"].features[constants.FOLDER_FEATURE] = "Work"
    test_qapp._qubes["dom0"].features[
        constants.FOLDER_ORDER_FEATURE
    ] = "Ungrouped Work"
    test_qapp._qubes["dom0"].features[
        constants.FOLDER_COLLAPSED_FEATURE
    ] = "Work"
    test_qapp.update_vm_calls()

    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    assert app_page.folder_order == ["Ungrouped", "Work"]
    assert app_page.collapsed_folders == {"Work"}

    app_page.toggle_buttons.templates_toggle.set_active(True)
    assert app_page.folder_order == [app_page.UNGROUPED, "Work"]
    assert app_page.collapsed_folders == {"Work"}

    app_page.toggle_buttons.system_toggle.set_active(True)
    assert app_page.folder_order == [app_page.UNGROUPED, "Work"]
    assert app_page.collapsed_folders == {"Work"}


def test_empty_folders_are_not_displayed(
    test_desktop_file_path, test_qapp, test_builder
):
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    app_page.toggle_buttons.apps_toggle.set_active(True)
    app_page._save_folder_state = mock.Mock()

    vm_entry = vm_manager.load_vm_from_name("test-red")
    assert vm_entry
    vm_entry.vm.features = {}

    # a folder with no assigned qube is never shown
    app_page._create_folder("Empty")
    assert "Empty" not in app_page.folder_order

    app_page._assign_folder(vm_entry, "Work")
    assert app_page.folder_order == [app_page.UNGROUPED, "Work"]

    # moving the last qube out removes the folder instead of showing an
    # empty section
    app_page._assign_folder(vm_entry, "")
    assert app_page.folder_order == [app_page.UNGROUPED]
    assert app_page._vm_folder(vm_entry) == ""

    vm_entry.vm.features[constants.FOLDER_FEATURE] = "Other"
    app_page._load_folder_state()
    assert app_page.folder_order == [app_page.UNGROUPED, "Other"]


def test_folder_selection_menu_entries(
    test_desktop_file_path, test_qapp, test_builder
):
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    app_page.toggle_buttons.apps_toggle.set_active(True)
    app_page._save_folder_state = mock.Mock()

    vm_entry = vm_manager.load_vm_from_name("test-red")
    assert vm_entry
    vm_entry.vm.features = {}
    app_page._assign_folder(vm_entry, "Work")

    other_entry = vm_manager.load_vm_from_name("sys-usb")
    assert other_entry
    other_entry.vm.features = {}
    app_page._assign_folder(other_entry, "Personal")

    submenu = app_page._folder_selection_menu(vm_entry, include_remove=True)
    labels = [item.get_label() for item in submenu.get_children()]

    assert "Work" not in labels
    assert "Personal" in labels
    assert "Ungrouped" not in labels
    assert "Create new folder…" in labels
    assert "Remove from folder" in labels


def test_unknown_vm_folder_falls_back_to_ungrouped(
    test_desktop_file_path, test_qapp, test_builder
):
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    app_page.toggle_buttons.apps_toggle.set_active(True)

    vm_entry = vm_manager.load_vm_from_name("test-red")
    assert vm_entry
    vm_entry.vm.features = {constants.FOLDER_FEATURE: "MissingFolder"}

    vm_row = app_page.vm_rows["test-red"]

    assert app_page._effective_vm_folder(vm_entry) == app_page.UNGROUPED
    assert app_page._is_row_visible(vm_row)


def test_folder_list_roundtrip_with_space_and_backslash_in_names():
    """Folder names containing a literal space or backslash must survive the
    feature-value format: the escape character itself has to be escapable."""
    names = [
        "My Folder",
        "back\\slash",
        "space \\ and space",
        "plain",
        "Ungrouped",
    ]
    encoded = AppPage._encode_folder_list(names)
    # an unescaped space still separates entries; the escape character
    # itself is escaped, so backslashes in names stay literal
    assert AppPage._encode_folder_list(["My Folder"]) == r"My\ Folder"
    assert AppPage._encode_folder_list(["back\\slash"]) == r"back\\slash"
    assert AppPage._encode_folder_list(["space \\ and space"]) == (
        r"space\ \\\ and\ space"
    )
    assert AppPage._decode_folder_list(encoded) == names
    assert AppPage._encode_folder_list(["\\", " "]) == r"\\ \ "
    assert AppPage._decode_folder_list(r"\\ \ ") == ["\\", " "]
    assert AppPage._decode_folder_list(r"a\\ b c") == ["a\\", "b", "c"]
    assert AppPage._decode_folder_list(r"a\ b c") == ["a b", "c"]


def test_folder_state_with_names_containing_spaces(
    test_desktop_file_path, test_qapp, test_builder
):
    """menu-folder-order keeps folders with spaces as single entries."""
    dispatcher = MockDispatcher(test_qapp)
    vm_manager = VMManager(test_qapp, dispatcher)

    with mock.patch.object(
        DesktopFileManager, "desktop_dirs", [test_desktop_file_path]
    ):
        desktop_file_manager = DesktopFileManager(test_qapp)

    app_page = AppPage(vm_manager, test_builder, desktop_file_manager)
    app_page.toggle_buttons.apps_toggle.set_active(True)

    dom0_mock = test_qapp._qubes["dom0"]

    def fake_save():
        dom0_mock.features[constants.FOLDER_ORDER_FEATURE] = (
            AppPage._encode_folder_list(app_page.folder_order)
        )
        dom0_mock.features[constants.FOLDER_COLLAPSED_FEATURE] = (
            AppPage._encode_folder_list(app_page.collapsed_folders)
        )
        dom0_mock.update_calls()

    app_page._save_folder_state = fake_save

    vm_entry = vm_manager.load_vm_from_name("test-red")
    assert vm_entry
    vm_entry.vm.features = {}
    app_page._assign_folder(vm_entry, "sys usb")

    assert app_page.folder_order == [app_page.UNGROUPED, "sys usb"]
    # stored with the space escaped so it is not read back as two folders
    assert (
        dom0_mock.features[constants.FOLDER_ORDER_FEATURE]
        == "Ungrouped sys\\ usb"
    )

    # reloading reads it back as exactly one folder
    app_page._load_folder_state()
    assert app_page.folder_order == [app_page.UNGROUPED, "sys usb"]
