import pygst
pygst.require("0.10")
import gst

from freeseer.framework.plugin import IOutput

class OggIcecast(IOutput):
    name = "Ogg Icecast"
    type = "both"
    extension = "ogg"
    tags = None
    
    # Icecast server variables
    ip = "127.0.0.1"
    port = "8000"
    password = "hackme"
    mount = "/stream.ogg"
    
    def get_output_bin(self, metadata=None):
        bin = gst.Bin(self.name)
        
        if metadata is not None:
            self.set_metadata(metadata)
        
        # Setup Audio Pipeline
        audioqueue = gst.element_factory_make("queue", "audioqueue")
        bin.add(audioqueue)
        
        audioconvert = gst.element_factory_make("audioconvert", "audioconvert")
        bin.add(audioconvert)
        
        audiocodec = gst.element_factory_make("vorbisenc", "audiocodec")
        bin.add(audiocodec)
        
        # Setup Video Pipeline
        videoqueue = gst.element_factory_make("queue", "videoqueue")
        bin.add(videoqueue)
        
        videocodec = gst.element_factory_make("theoraenc", "videocodec")
        bin.add(videocodec)
        
        # Setup metadata
        vorbistag = gst.element_factory_make("vorbistag", "vorbistag")
        # set tag merge mode to GST_TAG_MERGE_REPLACE
        merge_mode = gst.TagMergeMode.__enum_values__[2]

        vorbistag.merge_tags(self.tags, merge_mode)
        vorbistag.set_tag_merge_mode(merge_mode)
        bin.add(vorbistag)
        
        # Muxer
        muxer = gst.element_factory_make("oggmux", "muxer")
        bin.add(muxer)
        
        icecast = gst.element_factory_make("shout2send", "icecast")
        icecast.set_property("ip", self.ip)
        icecast.set_property("port", self.port)
        icecast.set_property("password", self.password)
        icecast.set_property("mount", self.mount)
        bin.add(icecast)
        
        # Setup ghost pads
        audiopad = audioqueue.get_pad("sink")
        audio_ghostpad = gst.GhostPad("audiosink", audiopad)
        bin.add_pad(audio_ghostpad)
        
        videopad = videoqueue.get_pad("sink")
        video_ghostpad = gst.GhostPad("videosink", videopad)
        bin.add_pad(video_ghostpad)
        
        gst.element_link_many(audioqueue, audioconvert, audiocodec, vorbistag, muxer)
        gst.element_link_many(videoqueue, videocodec, muxer)
        gst.element_link_many(muxer, icecast)
        
        return bin
    
    def set_metadata(self, data):
        '''
        Populate global tag list variable with file metadata for
        vorbistag audio element
        '''
        self.tags = gst.TagList()

        for tag in data.keys():
            if(gst.tag_exists(tag)):
                self.tags[tag] = data[tag]
            else:
                #self.core.logger.log.debug("WARNING: Tag \"" + str(tag) + "\" is not registered with gstreamer.")
                pass
