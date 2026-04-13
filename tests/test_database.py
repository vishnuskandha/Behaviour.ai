def test_db_manager(manager):
    assert manager._db is not None
    stats = manager.get_statistics()
    assert 'total_users' in stats
