def test_train_model(manager):
    result = manager.train_model()
    assert result['status'] == 'success'
    assert 'accuracy' in result
    assert result['accuracy'] > 0
