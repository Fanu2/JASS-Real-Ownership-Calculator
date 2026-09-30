from decimal import Decimal, ROUND_HALF_UP
import re

SAR_PER_MARLA = Decimal("9")
MARLA_PER_KANAL = Decimal("20")
SAR_PER_KANAL = Decimal("180")

def area_to_sar(kanal, marla, sar=0):
    return Decimal(str(kanal or 0))*SAR_PER_KANAL + Decimal(str(marla or 0))*SAR_PER_MARLA + Decimal(str(sar or 0))

def fraction_value(value):
    if value is None:
        return None
    m=re.search(r'(\d+)\s*/\s*(\d+)', str(value))
    if not m:
        return None
    n,d=int(m.group(1)),int(m.group(2))
    if d==0:
        return None
    return Decimal(n)/Decimal(d)

def parse_area(value):
    if not value:
        return None
    s=str(value).replace("\xa0"," ").strip()
    m=re.match(r'^\s*(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?', s)
    if not m:
        return None
    return area_to_sar(m.group(1),m.group(2),m.group(3) or 0)

def format_kms(value):
    if value is None:
        return ""
    total=int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    k,rem=divmod(total,180)
    m,s=divmod(rem,9)
    return f"{k}-{m}-{s}"

def fraction_text(value, denominator=Decimal(1)):
    if value is None or denominator == 0:
        return ""
    f=(Decimal(value)/Decimal(denominator))
    # Show a compact decimal-free fraction when it is exact enough.
    from fractions import Fraction
    q=Fraction(str(f)).limit_denominator(1000000)
    return f"{q.numerator}/{q.denominator}"
