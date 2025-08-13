try:
    import ui.main_interface
    print('Module imported successfully')
    print('Module contents:', dir(ui.main_interface))
    
    try:
        from ui.main_interface import MainInterface
        print('MainInterface imported successfully')
        print('MainInterface:', MainInterface)
    except Exception as e:
        print('MainInterface import error:', e)
        
except Exception as e:
    print('Module import error:', e)
    import traceback
    traceback.print_exc()