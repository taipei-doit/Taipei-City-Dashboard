CREATE TABLE public.uv (
    StationName VARCHAR(255),
    StationId VARCHAR(255),
    ObsTime TIMESTAMP,
    Lat DECIMAL(10, 6),
    Lon DECIMAL(10, 6),
    District VARCHAR(255),
    City VARCHAR(255),
    DistrictCode VARCHAR(255),
    CityCode VARCHAR(255),
    UVIndex FLOAT
);