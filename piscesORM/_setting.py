

class Global_setting:
    """
    PiscesORM Global Settings
    """

    lock_auto_release_time = 0 # seconds
    """ Maximum time a lock can be held before it is automatically released. Set 0 to disable auto release. (sec, float)"""
    garbage_clean_cycle = 5 # seconds
    """ Time between lock data garbage collection cycles (sec, float)"""
    modified_obj_output = False
    """ Using beautified output, you can visually see the information when you print(table)."""
    
    

setting = Global_setting()