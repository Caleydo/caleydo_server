from phovea_server.util import jsonify


class TestCustomEncoders:
  def test_sets(self):
    assert jsonify(list(set())) == []

  def test_nan_values(self):
    assert float('nan') is None
