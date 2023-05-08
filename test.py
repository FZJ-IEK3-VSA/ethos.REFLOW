# test imports
import sys
print("Python sys.path:", sys.path)

def test_imports():
    import sys
    print("Python sys.path:", sys.path)
    import geokit as gk
    import glaes as gl
    import reskit as rk
    # if test reached here, imports worked. 
    assert True