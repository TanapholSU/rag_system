from api.service.storage import prepend_unique_id_to_filename


def test_prepend_unique_id_to_filename():
    result = prepend_unique_id_to_filename("file.txt")
    uuid_part, filename = result.split("_")

    assert len(uuid_part) == 36
    assert filename == "file.txt"
