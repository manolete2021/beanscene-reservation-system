"""Tests for the member directory: custom sort and binary search."""

from beanscene import member_directory
from beanscene.records import make_member


def sample_members():
    return [make_member(1007, "Siobhan", "O'Brien"), make_member(1003, "Liam", "Obrien"),
            make_member(1012, "Grace", "O-Brien"), make_member(1001, "Aisha", "Khan"),
            make_member(1009, "Marco", "Rossi"), make_member(1008, "Ben", "Abbott"),
            make_member(1013, "Nora", "Ocampo"), make_member(1014, "Sam", "Obama")]


def test_surname_key_ignores_capitals_apostrophes_and_hyphens():
    keys = {member_directory.surname_key(name) for name in ["O'Brien", "Obrien", "O-Brien", "OBRIEN"]}
    assert keys == {"obrien"}


def test_obrien_spellings_file_together():
    directory = member_directory.build_directory(sample_members())
    surnames = [member["surname"] for member in directory["by_surname"]]
    assert surnames == ["Abbott", "Khan", "Obama", "O-Brien", "Obrien", "O'Brien", "Ocampo", "Rossi"]


def test_custom_sort_by_number():
    sorted_members = member_directory.custom_sort(sample_members(), "number")
    numbers = [member["number"] for member in sorted_members]
    assert numbers == [1001, 1003, 1007, 1008, 1009, 1012, 1013, 1014]


def test_binary_search_finds_every_member_in_few_steps():
    directory = member_directory.build_directory(sample_members())
    for member in sample_members():
        found, steps = member_directory.binary_search_by_number(directory, member["number"])
        assert found["number"] == member["number"]
        assert steps <= 4


def test_missing_member_is_not_found():
    directory = member_directory.build_directory(sample_members())
    assert member_directory.find_member(directory, 9999) is None


def test_add_member_keeps_both_lists_sorted():
    directory = member_directory.build_directory(sample_members())
    number = member_directory.next_member_number(directory)
    member_directory.add_member(directory, make_member(number, "Dara", "O'brien"))
    assert member_directory.find_member(directory, number)["first_name"] == "Dara"
    values = [member_directory.sort_value(m, "surname") for m in directory["by_surname"]]
    assert values == sorted(values)


def test_report_has_headings():
    report = member_directory.directory_report(member_directory.build_directory(sample_members()))
    assert report.splitlines()[0].split() == ["Surname", "First", "name", "Member", "no.", "Phone"]
