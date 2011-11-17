from django.http import HttpResponse


def __main__( request, actions, lonmax, lonmin, latmax, latmin ):
    
    actions.discard("kml")
    where = request.get_full_path()
    where = where.replace("kml,", "")
    where = where.replace("kml", "")
    where = where.replace("&", "&amp;")
    kml = ('''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Folder>
<name>fvcom overlays</name>
<description>Requested plot of fvcom data</description>
<GroundOverlay>
  <name>FVCOM</name>
  <description>Display of processed fvcom data from requested kml.</description>
  <Icon>
    <href>http://localhost:8000''' + where + '''</href>
  </Icon>
  <LatLonBox>
    <north>''' + str(latmax) + '''</north>
    <south>''' + str(latmin) + '''</south>
    <east>''' + str(lonmax) + '''</east>
    <west>''' + str(lonmin) + '''</west>
    
  </LatLonBox>
</GroundOverlay>
</Folder>
</kml>
    ''')
    
    response = HttpResponse(content_type="application/vnd.google-earth.kml+xml")
    response['Content-Disposition'] = 'filename=fvcom.kml'
    response.write(kml)
    
    return response, request, actions