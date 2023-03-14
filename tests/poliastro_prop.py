"""Test poliastro sgp4 propagation of TLE's"""
from astropy import units as u
from poliastro.bodies import Earth
from poliastro.twobody import Orbit
from sgp4.api import Satrec, jday

tle_1 = "1 22566U 93016B   23061.82868274  .00000284  00000-0  17111-3 0  9995"
tle_2 = "2 22566  71.0096  10.9886 0011485 211.9224 148.1204 14.15038904546143"
sat = Satrec.twoline2rv(tle_1, tle_2)

jd1, fr1 = jday(2023, 3, 4, 12, 0, 0)
error1, r1, v1 = sat.sgp4(jd1, fr1)
assert error1 == 0
orb1 = Orbit.from_vectors(Earth, r1 << u.km, v1 << u.km / u.s)

jd2, fr2 = jday(2310, 3, 4, 12, 0, 0)
error2, r2, v2 = sat.sgp4(jd2, fr2)
assert error2 == 0
orb2 = Orbit.from_vectors(Earth, r2 << u.km, v2 << u.km / u.s)

print(orb1.a << u.km)
print(orb2.a << u.km)
