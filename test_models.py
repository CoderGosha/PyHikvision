from model import CMSearchResult

search_picture = """
<CMSearchResult version="1.0" xmlns="urn:psialliance-org">
<searchID>{b7fd59ec-0a8a-4bd5-b5af-9c1018652d12}</searchID>
<responseStatus>true</responseStatus>
<numOfMatches>2</numOfMatches>
<responseStatusStrg>MORE</responseStatusStrg>
<matchList>
<searchMatchItem>
<sourceID>{0000000000-0000-0000-0000-000000000000}</sourceID>
<trackID>120</trackID>
<timeSpan>
<startTime>2022-12-06T08:51:13Z</startTime>
<endTime>2022-12-06T08:51:13Z</endTime>
</timeSpan>
<mediaSegmentDescriptor>
<contentType>video</contentType>
<codecType>H.264-BP</codecType>
<playbackURI>rtsp://192.168.0.221/Streaming/tracks/120?starttime=2022-12-06T08:51:13Z&amp;endtime=2022-12-06T08:51:13Z&amp;name=20221206085113_00260876_00_00_SC_01&amp;size=322560</playbackURI>
</mediaSegmentDescriptor>
<metadataMatches>
<metadataDescriptor>recordType.meta.hikvision.com/timing</metadataDescriptor>
</metadataMatches>
</searchMatchItem>
<searchMatchItem>
<sourceID>{0000000000-0000-0000-0000-000000000000}</sourceID>
<trackID>120</trackID>
<timeSpan>
<startTime>2022-12-06T08:54:19Z</startTime>
<endTime>2022-12-06T08:54:19Z</endTime>
</timeSpan>
<mediaSegmentDescriptor>
<contentType>video</contentType>
<codecType>H.264-BP</codecType>
<playbackURI>rtsp://192.168.0.221/Streaming/tracks/120?starttime=2022-12-06T08:54:19Z&amp;endtime=2022-12-06T08:54:19Z&amp;name=20221206085419_00261046_00_00_SC_01&amp;size=258048</playbackURI>
</mediaSegmentDescriptor>
<metadataMatches>
<metadataDescriptor>recordType.meta.hikvision.com/timing</metadataDescriptor>
</metadataMatches>
</searchMatchItem>
</matchList>
</CMSearchResult>
"""


search_picture2 = """
<CMSearchResult version="1.0" xmlns="urn:psialliance-org">

<searchID>{3eeda297-390d-40c7-95e1-674897a01769}</searchID>

<responseStatus>true</responseStatus>

<numOfMatches>1</numOfMatches>

<responseStatusStrg>OK</responseStatusStrg>

<matchList>
<searchMatchItem>
<sourceID>{0000000000-0000-0000-0000-000000000000}</sourceID>
<trackID>120</trackID>
<timeSpan>
<startTime>2022-12-07T13:43:30Z</startTime>

<endTime>2022-12-07T13:43:30Z</endTime>

</timeSpan>

<mediaSegmentDescriptor>

<contentType>video</contentType>

<codecType>H.264-BP</codecType>

<playbackURI>rtsp://192.168.0.221/Streaming/tracks/120?starttime=2022-12-07T13:43:30Z&amp;endtime=2022-12-07T13:43:30Z&amp;name=20221207134330_00431097_00_00_SC_01&amp;size=442368</playbackURI>

</mediaSegmentDescriptor>

<metadataMatches>

<metadataDescriptor>recordType.meta.hikvision.com/timing</metadataDescriptor>

</metadataMatches>

</searchMatchItem>

</matchList>

</CMSearchResult>
"""
if __name__ == '__main__':
    s = CMSearchResult.from_xml_str(search_picture2)
    print(f"Id: {s.search_id}, count: {s.count} list {s.search_list}")
    for e in s.search_list:
        print(f"Id: {e.track_id}, time: {e.time_start}, playback: {e.play_back_uri}, description: {e.description}")