import pytest

@pytest.mark.mock_data
def test_without_marker():
    """Test basic assertion without external dependencies"""
    assert True
