from app.land_math import area_to_sar,parse_area,format_kms,fraction_value
def test_area():
    assert area_to_sar(1,0)==180
    assert area_to_sar(0,1)==9
def test_format():
    assert format_kms("3.999999999")=="0-0-4"
    assert format_kms("8.999999999")=="0-1-0"
def test_fraction():
    assert fraction_value("5/6 भाग") == 5/6
def test_parse_area():
    assert parse_area("4-0 नहरी")==720
