import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  Alert,
  Linking,
  Dimensions,
  Share,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Chip,
  FAB,
  Portal,
  Modal,
  TextInput,
  RadioButton,
  Divider,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';
import FastImage from 'react-native-fast-image';
import Video from 'react-native-video';
import { showMessage } from 'react-native-flash-message';
import { useApi, Post } from '../context/ApiContext';
import { theme, spacing, borderRadius, shadows } from '../theme';
import HapticFeedback from 'react-native-haptic-feedback';

const { width } = Dimensions.get('window');

const ConfirmedScreen: React.FC = () => {
  const { state, fetchPosts, performAction, refreshData } = useApi();
  const [refreshing, setRefreshing] = useState(false);
  const [posts, setPosts] = useState<Post[]>([]);

  useEffect(() => {
    loadConfirmedPosts();
  }, []);

  const loadConfirmedPosts = useCallback(async () => {
    try {
      await fetchPosts('posted');
      setPosts(state.posts.filter(post => post.status === 'posted'));
    } catch (error) {
      console.error('Error loading confirmed posts:', error);
    }
  }, [fetchPosts, state.posts]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refreshData();
    await loadConfirmedPosts();
    setRefreshing(false);
  }, [refreshData, loadConfirmedPosts]);

  const handlePostAction = async (post: Post, actionType: string) => {
    try {
      HapticFeedback.trigger('impactLight');
      
      if (actionType === 'post_twitter') {
        if (post.translated_text) {
          const tweetText = encodeURIComponent(post.translated_text);
          const tweetUrl = `https://x.com/intent/tweet?text=${tweetText}`;
          
          const canOpen = await Linking.canOpenURL(tweetUrl);
          if (canOpen) {
            await Linking.openURL(tweetUrl);
          } else {
            const fallbackUrl = `https://twitter.com/intent/tweet?text=${tweetText}`;
            await Linking.openURL(fallbackUrl);
          }
          
          await performAction(post.id, 'post_twitter', '', tweetUrl);
        } else {
          showMessage({
            message: 'No translated text available for posting',
            type: 'warning',
          });
        }
      } else {
        await performAction(post.id, actionType);
      }
      
      await loadConfirmedPosts();
    } catch (error) {
      console.error('Error performing action:', error);
      showMessage({
        message: 'Error performing action',
        type: 'danger',
      });
    }
  };

  const handleSaveMedia = async (post: Post, mediaType: 'image' | 'video') => {
    try {
      HapticFeedback.trigger('impactLight');
      
      if (post.media_path) {
        const mediaUrl = `${state.apiUrl}/api/media/${post.media_path}`;
        
        await Share.share({
          url: mediaUrl,
          title: `Save ${mediaType}`,
        });
      }
    } catch (error) {
      console.error('Error saving media:', error);
      showMessage({
        message: 'Error saving media',
        type: 'danger',
      });
    }
  };

  const renderMedia = (post: Post) => {
    if (!post.media_path) return null;

    const mediaUrl = `${state.apiUrl}/api/media/${post.media_path}`;

    if (post.media_type === 'photo') {
      return (
        <View style={styles.mediaContainer}>
          <FastImage
            source={{ uri: mediaUrl }}
            style={styles.mediaImage}
            resizeMode={FastImage.resizeMode.cover}
            onError={(error) => {
              console.log('Image load error:', error);
            }}
          />
        </View>
      );
    } else if (post.media_type === 'video') {
      return (
        <View style={styles.mediaContainer}>
          <Video
            source={{ uri: mediaUrl }}
            style={styles.mediaVideo}
            controls={true}
            resizeMode="cover"
            onError={(error) => {
              console.log('Video load error:', error);
            }}
          />
        </View>
      );
    }

    return null;
  };

  const renderPost = ({ item: post }: { item: Post }) => (
    <Card style={styles.postCard}>
      <Card.Content>
        <View style={styles.postHeader}>
          <Text style={styles.channelName}>{post.channel_name}</Text>
          <Text style={styles.postDate}>{formatDate(post.created_at)}</Text>
        </View>

        {post.translated_text && (
          <View style={styles.contentContainer}>
            <Text style={styles.contentLabel}>Content:</Text>
            <Text style={styles.contentText}>{post.translated_text}</Text>
          </View>
        )}

        <View style={styles.statusContainer}>
          <Chip
            style={[styles.statusChip, styles.statusConfirmed]}
            textStyle={styles.statusText}
          >
            CONFIRMED
          </Chip>
          {post.quality_score && (
            <Text style={styles.qualityScore}>
              Quality: {Math.round(post.quality_score * 100)}%
            </Text>
          )}
        </View>

        {renderMedia(post)}

        <View style={styles.actionButtons}>
          <Button
            mode="contained"
            onPress={() => handlePostAction(post, 'post_twitter')}
            style={styles.actionButton}
            labelStyle={styles.actionButtonText}
          >
            Tweet
          </Button>
          
          <Button
            mode="outlined"
            onPress={() => handlePostAction(post, 'reject')}
            style={styles.actionButton}
            labelStyle={styles.actionButtonText}
          >
            Reject
          </Button>
          
          <Button
            mode="outlined"
            onPress={() => handlePostAction(post, 'archive')}
            style={styles.actionButton}
            labelStyle={styles.actionButtonText}
          >
            Duplicate
          </Button>
          
          {post.media_path && (
            <Button
              mode="outlined"
              onPress={() => handleSaveMedia(post, post.media_type === 'photo' ? 'image' : 'video')}
              style={styles.actionButton}
              labelStyle={styles.actionButtonText}
            >
              Save {post.media_type === 'photo' ? 'Image' : 'Video'}
            </Button>
          )}
        </View>
      </Card.Content>
    </Card>
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={posts}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderPost}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[theme.colors.primary]}
          />
        }
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              No confirmed posts available yet. Posts appear here after being accepted and rewritten by OpenAI.
            </Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  listContainer: {
    padding: spacing.md,
  },
  postCard: {
    marginBottom: spacing.md,
    backgroundColor: theme.colors.surface,
    ...shadows.medium,
  },
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  channelName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  postDate: {
    fontSize: 12,
    color: theme.colors.text,
    opacity: 0.7,
  },
  contentContainer: {
    marginBottom: spacing.sm,
  },
  contentLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: 4,
  },
  contentText: {
    fontSize: 14,
    color: theme.colors.text,
    lineHeight: 20,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  statusChip: {
    marginRight: spacing.sm,
  },
  statusConfirmed: {
    backgroundColor: '#1b2d1b',
  },
  statusText: {
    color: '#4caf50',
    fontSize: 12,
    fontWeight: 'bold',
  },
  qualityScore: {
    fontSize: 12,
    color: theme.colors.text,
    opacity: 0.7,
  },
  mediaContainer: {
    marginVertical: spacing.sm,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
  },
  mediaImage: {
    width: '100%',
    height: 200,
  },
  mediaVideo: {
    width: '100%',
    height: 200,
  },
  actionButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  actionButton: {
    flex: 0,
    minWidth: 80,
  },
  actionButtonText: {
    fontSize: 12,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  emptyText: {
    fontSize: 16,
    color: theme.colors.text,
    textAlign: 'center',
    opacity: 0.7,
  },
});

export default ConfirmedScreen; 