import functools

import numpy

from openfisca_core import periods
from openfisca_core.data_storage import OnDiskStorage
from openfisca_core.indexed_enums import Enum, EnumArray

import pytest


@pytest.fixture
def storage():
    return functools.partial(OnDiskStorage, storage_dir = "/tmp")


@pytest.fixture
def eternal_storage(storage):
    return functools.partial(storage, is_eternal = True)


@pytest.fixture
def period():
    return periods.period("2020")


@pytest.fixture
def eternal_period():
    return periods.period(periods.ETERNITY)


@pytest.fixture
def value():
    return numpy.array([1])


@pytest.fixture
def file(storage, period):
    return f"{storage().storage.directory}/{period}.npy"


@pytest.fixture
def eternal_file(storage, eternal_period):
    return f"{storage().storage.directory}/{str(eternal_period)}.npy"


@pytest.fixture
def my_enum():
    class MyEnum(Enum):
        foo = "foo"
        bar = "bar"

    return MyEnum


@pytest.fixture
def enum_array(value, my_enum):
    return EnumArray(value, my_enum)


def test___init__(storage):
    result = storage()

    assert result


def test___init__when_is_eternal(eternal_storage):
    result = eternal_storage()

    assert result.is_eternal


def test__init__when_preserve_storage_dir(storage):
    result = storage(preserve_storage_dir = True)

    assert result.storage.preserve


def test_get(storage, period, file, enum_array, mocker):
    storage = storage()
    files = {period: (file, enum_array)}
    mocker.patch.dict(storage._files, files)
    mocker.patch.object(storage.storage, "get", autospec = True)
    storage.get(period)

    result = files, period

    storage.storage.get.assert_called_once_with(*result)


def test_get_when_is_eternal(eternal_storage, period, eternal_period, file, mocker):
    """When it is eternal, periods are actually ignored"""
    storage = eternal_storage()
    files = {period: (file, None)}
    mocker.patch.dict(storage._files, files)
    mocker.patch.object(storage.storage, "get", autospec = True)
    storage.get(period)

    result = files, eternal_period

    storage.storage.get.assert_called_once_with(*result)


def test_get_when_cache_is_empty(storage, period):
    storage = storage()

    result = storage.get(period)

    assert not result


def test_put(storage, period, value, file, mocker):
    storage = storage()
    mocker.patch("numpy.save")
    storage.put(value, period)

    result = file, value

    numpy.save.assert_called_once_with(*result)


def test_put_when_is_eternal(eternal_storage, period, value, eternal_file, mocker):
    """When it is eternal, periods are actually ignored"""
    storage = eternal_storage()
    mocker.patch("numpy.save")
    storage.put(value, period)

    result = eternal_file, value

    numpy.save.assert_called_once_with(*result)


def test_delete(storage, period, file, mocker):
    storage = storage()
    files = {period: file, period.last_year: file}
    mocker.patch.dict(storage._files, files)
    mocker.patch.object(storage.storage, "delete", autospec = True)
    storage.delete(period)

    result = files, period

    storage.storage.delete.assert_called_once_with(*result)


def test_delete_when_period_is_not_specified(storage, period, file, mocker):
    storage = storage()
    files = {period: file, period.last_year: file}
    mocker.patch.dict(storage._files, files)
    storage.delete()

    result = storage.get(period), storage.get(period.last_year)

    assert result == (None, None)


def test_delete_when_is_eternal(eternal_storage, value, eternal_period, mocker):
    """When it is eternal, periods are actually ignored"""
    storage = eternal_storage()
    files = {period: file, eternal_period: file}
    mocker.patch.dict(storage._files, files)
    mocker.patch.object(storage.storage, "delete", autospec = True)
    storage.delete(period)

    result = files, eternal_period

    storage.storage.delete.assert_called_once_with(*result)


def test_get_known_periods(storage, period, file, mocker):
    storage = storage()
    files = {period: file}
    mocker.patch.dict(storage._files, files)

    result = storage.get_known_periods()

    assert list(result) == [period]


def test_get_memory_usage(storage, period, eternal_period, file, value, mocker):
    storage = storage()
    files = {period: file, eternal_period: file}
    mocker.patch.dict(storage._files, files)
    mocker.patch("os.path.getsize", return_value = 8)
    mocker.patch.object(storage, "_decode_file", return_value = value)

    result = storage.get_memory_usage()

    assert result == {
        "nb_files": 2,
        "total_nb_bytes": 16,
        "cell_size": 8,
        }