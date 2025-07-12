import React from 'react';
import { View } from 'react-native';

const VideoWeb = ({ source, style, resizeMode, controls, paused, ...props }) => {
  return (
    <View style={style}>
      <video
        src={source.uri}
        controls={controls}
        autoPlay={!paused}
        style={{
          width: '100%',
          height: '100%',
          objectFit: resizeMode === 'contain' ? 'contain' : 'cover',
        }}
        {...props}
      />
    </View>
  );
};

export default VideoWeb; 