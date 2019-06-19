import pytest
import numpy as np

from hnccorr.embedding import CorrelationEmbedding, exponential_distance_decay


@pytest.fixture
def mock_patch(mocker, dummy):
    return mocker.patch("hnccorr.movie.Patch", autospec=True)(dummy, dummy, dummy)


@pytest.fixture
def CE1(mock_patch):
    mock_patch.pixel_shape = (7,)
    mock_patch.__getitem__.return_value = np.array(
        [
            [1, 1, 1, 1, 1, 1, 1],
            [-1, -1, -1, -1, -1, -1, -1],
            [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        ]
    )

    return CorrelationEmbedding(mock_patch)


@pytest.fixture
def CE2(mock_patch):
    mock_patch.pixel_shape = (3, 3)
    mock_patch.__getitem__.return_value = np.zeros((3, 3))
    return CorrelationEmbedding(mock_patch)


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_embedding(CE1, CE2, mock_patch):

    np.testing.assert_allclose(
        CE1.embedding[0],
        [1.0, 0.99833749, 0.99339927, 0.98532928, 0.9743547, 0.96076892, 0.94491118],
    )

    np.testing.assert_allclose(CE2.embedding[(0, 0, slice(None, None))], [0, 0, 0])


def test_get_vector(CE1):
    CE1.embedding = np.array([[0.0, 1.0], [-2.0, 0.0]])
    np.testing.assert_allclose(CE1.get_vector((0,)), np.array([0.0, -2.0]))


def test_exponential_distance_decay():
    alpha = 0.5

    exponential_distance_decay(
        np.array([0.0, -2.0]), np.array([[1.0, 0.0]]), alpha
    ) == pytest.approx(np.exp(-0.25))
