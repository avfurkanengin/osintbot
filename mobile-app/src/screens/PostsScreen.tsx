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

const PostsScreen: React.FC = () => {
  const { state, fetchPosts, performAction, batchAction, refreshData } = useApi();
  const [refreshing, setRefreshing] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string>('pending');
  const [selectedPosts, setSelectedPosts] = useState<number[]>([]);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [showActionModal, setShowActionModal] = useState(false);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [actionNotes, setActionNotes] = useState('');
  const [selectedAction, setSelectedAction] = useState('');
  const [batchActionType, setBatchAction] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [sortBy, setSortBy] = useState<'date' | 'quality' | 'priority'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    loadPosts();
  }, [selectedStatus]);

  const loadPosts = useCallback(async () => {
    await fetchPosts(selectedStatus === 'all' ? undefined : selectedStatus);
  }, [selectedStatus, fetchPosts]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refreshData();
    setRefreshing(false);
  }, [refreshData]);

  const handlePostAction = async (post: Post, actionType: string) => {
    HapticFeedback.trigger('impactMedium');
    
    if (actionType === 'post_twitter') {
      // Open X (Twitter) intent URL with proper encoding
      const twitterUrl = `https://x.com/intent/tweet?text=${encodeURIComponent(post.translated_text)}`;
      try {
        await Linking.openURL(twitterUrl);
        // Mark as posted
        await performAction(post.id, 'post_twitter', '', twitterUrl);
      } catch (error) {
        console.error('Failed to open X:', error);
        // Fallback to old twitter.com URL
        const fallbackUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(post.translated_text)}`;
        try {
          await Linking.openURL(fallbackUrl);
          await performAction(post.id, 'post_twitter', '', fallbackUrl);
        } catch (fallbackError) {
          console.error('Failed to open Twitter fallback:', fallbackError);
        }
      }
    } else {
      await performAction(post.id, actionType, actionNotes);
      setActionNotes('');
    }
  };

  const handleBatchAction = async () => {
    if (selectedPosts.length === 0) return;
    
    HapticFeedback.trigger('impactHeavy');
    await batchAction(selectedPosts, batchActionType, actionNotes);
    setSelectedPosts([]);
    setShowBatchModal(false);
    setActionNotes('');
  };

  const togglePostSelection = (postId: number) => {
    HapticFeedback.trigger('impactLight');
    setSelectedPosts(prev =>
      prev.includes(postId)
        ? prev.filter(id => id !== postId)
        : [...prev, postId]
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return theme.colors.warning;
      case 'posted': return theme.colors.success;
      case 'deleted': return theme.colors.error;
      case 'archived': return '#9E9E9E';
      case 'rejected': return '#FF5722';
      default: return theme.colors.primary;
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return theme.colors.success;
    if (score >= 0.6) return theme.colors.warning;
    return theme.colors.error;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleSaveMedia = async (post: Post, mediaType: 'image' | 'video') => {
    if (!post.media_path) return;

    const mediaUri = `${state.apiUrl}/api/media/${post.media_path}`;
    
    try {
      HapticFeedback.trigger('impactLight');
      
      // For React Native, we'll use the Share API to save/share the media
      await Share.share({
        url: mediaUri,
        message: `Media from ${post.channel_name}`,
      });
      
      showMessage({
        message: `${mediaType === 'image' ? 'Image' : 'Video'} shared successfully`,
        type: 'success',
      });
    } catch (error) {
      console.error('Failed to save media:', error);
      showMessage({
        message: `Failed to save ${mediaType}`,
        type: 'danger',
      });
    }
  };

  const renderMedia = (post: Post) => {
    if (!post.media_path) {
      return null;
    }

    const mediaUri = `${state.apiUrl}/api/media/${post.media_path}`;

    return (
      <View style={styles.mediaContainer}>
        {post.media_type === 'video' ? (
          <Video
            source={{ uri: mediaUri }}
            style={styles.media}
            resizeMode="contain"
            controls
            paused
            onError={(error) => {
              console.error('Video error:', error);
            }}
            onLoad={() => {
              console.log('Video loaded successfully');
            }}
          />
        ) : post.media_type === 'photo' ? (
          <FastImage
            source={{ 
              uri: mediaUri,
              priority: FastImage.priority.normal,
            }}
            style={styles.media}
            resizeMode={FastImage.resizeMode.contain}
            onError={() => {
              console.error('Image failed to load:', mediaUri);
            }}
            onLoad={() => {
              console.log('Image loaded successfully');
            }}
          />
        ) : null}
      </View>
    );
  };

  const renderPost = ({ item: post }: { item: Post }) => {
    const isSelected = selectedPosts.includes(post.id);
    
    return (
      <Card style={[styles.postCard, isSelected && styles.selectedCard]}>
        <Card.Content>
          <View style={styles.postHeader}>
            <View style={styles.postInfo}>
              <Title style={styles.channelName}>{post.channel_name}</Title>
              <Text style={styles.senderName}>{post.sender_name}</Text>
              <Text style={styles.dateText}>{formatDate(post.created_at)}</Text>
            </View>
            <TouchableOpacity
              style={styles.selectButton}
              onPress={() => togglePostSelection(post.id)}
            >
              <Icon
                name={isSelected ? 'check-circle' : 'radio-button-unchecked'}
                size={24}
                color={isSelected ? theme.colors.primary : '#9E9E9E'}
              />
            </TouchableOpacity>
          </View>

          <View style={styles.statusRow}>
            <Chip
              style={[styles.statusChip, { backgroundColor: getStatusColor(post.status) }]}
              textStyle={styles.chipText}
            >
              {post.status.toUpperCase()}
            </Chip>
            <Chip
              style={[styles.qualityChip, { backgroundColor: getQualityColor(post.quality_score) }]}
              textStyle={styles.chipText}
            >
              Q: {(post.quality_score * 100).toFixed(0)}%
            </Chip>
            <Chip
              style={styles.priorityChip}
              textStyle={styles.chipText}
            >
              P{post.priority}
            </Chip>
          </View>

          {post.translated_text && (
            <View style={styles.translatedSection}>
              <Text style={styles.translatedLabel}>Content:</Text>
              <Paragraph style={styles.translatedText}>{post.translated_text}</Paragraph>
            </View>
          )}

          {renderMedia(post)}

          <View style={styles.actionButtons}>
            <Button
              mode="contained"
              icon="twitter"
              style={[styles.actionButton, styles.twitterButton]}
              onPress={() => handlePostAction(post, 'post_twitter')}
              disabled={post.status === 'posted'}
            >
              Tweet
            </Button>
            {post.media_type === 'photo' && (
              <Button
                mode="outlined"
                icon="download"
                style={[styles.actionButton, styles.saveImageButton]}
                onPress={() => handleSaveMedia(post, 'image')}
              >
                Save Image
              </Button>
            )}
            {post.media_type === 'video' && (
              <Button
                mode="outlined"
                icon="download"
                style={[styles.actionButton, styles.saveVideoButton]}
                onPress={() => handleSaveMedia(post, 'video')}
              >
                Save Video
              </Button>
            )}
            <Button
              mode="outlined"
              icon="delete"
              style={[styles.actionButton, styles.deleteButton]}
              onPress={() => handlePostAction(post, 'delete')}
              disabled={post.status === 'deleted'}
            >
              Delete
            </Button>
            <Button
              mode="outlined"
              icon="archive"
              style={[styles.actionButton, styles.archiveButton]}
              onPress={() => handlePostAction(post, 'archive')}
              disabled={post.status === 'archived'}
            >
              Archive
            </Button>
          </View>
        </Card.Content>
      </Card>
    );
  };

  const statusOptions = [
    { label: 'All', value: 'all' },
    { label: 'Pending', value: 'pending' },
    { label: 'Posted', value: 'posted' },
    { label: 'Deleted', value: 'deleted' },
    { label: 'Archived', value: 'archived' },
  ];

  const filterAndSortPosts = (posts: Post[]) => {
    let filteredPosts = [...posts];

    // Apply search filter
    if (searchQuery.trim()) {
      filteredPosts = filteredPosts.filter(post =>
        post.original_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.translated_text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.channel_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.sender_name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply sorting
    filteredPosts.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'quality':
          comparison = a.quality_score - b.quality_score;
          break;
        case 'priority':
          comparison = a.priority - b.priority;
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filteredPosts;
  };

  const displayPosts = filterAndSortPosts(state.posts);

  return (
    <View style={styles.container}>
      <View style={styles.filterRow}>
        <FlatList
          horizontal
          data={statusOptions}
          keyExtractor={(item) => item.value}
          renderItem={({ item }) => (
            <Chip
              selected={selectedStatus === item.value}
              onPress={() => setSelectedStatus(item.value)}
              style={styles.filterChip}
            >
              {item.label}
            </Chip>
          )}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterContainer}
        />
        <View style={styles.searchControls}>
          <TouchableOpacity
            style={styles.searchButton}
            onPress={() => setShowSearch(!showSearch)}
          >
            <Icon name="search" size={24} color={theme.colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.sortButton}
            onPress={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          >
            <Icon 
              name={sortOrder === 'asc' ? 'arrow-upward' : 'arrow-downward'} 
              size={24} 
              color={theme.colors.primary} 
            />
          </TouchableOpacity>
        </View>
      </View>

      {showSearch && (
        <View style={styles.searchRow}>
          <TextInput
            label="Search posts..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            style={styles.searchInput}
            right={
              searchQuery ? (
                <TextInput.Icon 
                  icon="close" 
                  onPress={() => setSearchQuery('')} 
                />
              ) : null
            }
          />
          <View style={styles.sortOptions}>
            <Chip
              selected={sortBy === 'date'}
              onPress={() => setSortBy('date')}
              style={styles.sortChip}
            >
              Date
            </Chip>
            <Chip
              selected={sortBy === 'quality'}
              onPress={() => setSortBy('quality')}
              style={styles.sortChip}
            >
              Quality
            </Chip>
            <Chip
              selected={sortBy === 'priority'}
              onPress={() => setSortBy('priority')}
              style={styles.sortChip}
            >
              Priority
            </Chip>
          </View>
        </View>
      )}

      <FlatList
        data={displayPosts}
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
              {searchQuery ? 'No posts match your search' : 'No posts available'}
            </Text>
          </View>
        }
      />

      {selectedPosts.length > 0 && (
        <FAB
          icon="playlist-check"
          label={`${selectedPosts.length} selected`}
          style={styles.fab}
          onPress={() => setShowBatchModal(true)}
        />
      )}

      <Portal>
        <Modal
          visible={showBatchModal}
          onDismiss={() => setShowBatchModal(false)}
          contentContainerStyle={styles.modalContainer}
        >
          <Title>Batch Action</Title>
          <Text>Select action for {selectedPosts.length} posts:</Text>
          
          <RadioButton.Group
            onValueChange={setBatchAction}
            value={batchActionType}
          >
            <View style={styles.radioOption}>
              <RadioButton value="delete" />
              <Text>Delete</Text>
            </View>
            <View style={styles.radioOption}>
              <RadioButton value="archive" />
              <Text>Archive</Text>
            </View>
            <View style={styles.radioOption}>
              <RadioButton value="approve" />
              <Text>Approve</Text>
            </View>
          </RadioButton.Group>

          <TextInput
            label="Notes (optional)"
            value={actionNotes}
            onChangeText={setActionNotes}
            multiline
            style={styles.notesInput}
          />

          <View style={styles.modalActions}>
            <Button onPress={() => setShowBatchModal(false)}>Cancel</Button>
            <Button
              mode="contained"
              onPress={handleBatchAction}
              disabled={!batchActionType}
            >
              Apply
            </Button>
          </View>
        </Modal>
      </Portal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  filterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  filterContainer: {
    paddingHorizontal: spacing.md,
  },
  filterChip: {
    marginRight: spacing.sm,
  },
  searchControls: {
    flexDirection: 'row',
    paddingHorizontal: spacing.md,
  },
  searchButton: {
    padding: spacing.xs,
    marginRight: spacing.sm,
  },
  sortButton: {
    padding: spacing.xs,
  },
  searchRow: {
    padding: spacing.md,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  searchInput: {
    marginBottom: spacing.sm,
  },
  sortOptions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  sortChip: {
    marginHorizontal: spacing.xs,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  emptyText: {
    fontSize: 16,
    color: theme.colors.text,
    opacity: 0.6,
  },
  listContainer: {
    padding: spacing.md,
  },
  postCard: {
    marginBottom: spacing.md,
    ...shadows.medium,
  },
  selectedCard: {
    borderColor: theme.colors.primary,
    borderWidth: 2,
  },
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  postInfo: {
    flex: 1,
  },
  channelName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  senderName: {
    fontSize: 14,
    color: theme.colors.text,
    opacity: 0.7,
  },
  dateText: {
    fontSize: 12,
    color: theme.colors.text,
    opacity: 0.5,
  },
  selectButton: {
    padding: spacing.xs,
  },
  statusRow: {
    flexDirection: 'row',
    marginBottom: spacing.sm,
  },
  statusChip: {
    marginRight: spacing.xs,
  },
  qualityChip: {
    marginRight: spacing.xs,
  },
  priorityChip: {
    backgroundColor: theme.colors.surface,
  },
  chipText: {
    fontSize: 12,
    color: 'white',
    fontWeight: 'bold',
  },
  originalText: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: spacing.sm,
  },
  translatedSection: {
    backgroundColor: '#F5F5F5',
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.sm,
  },
  translatedLabel: {
    fontSize: 12,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: spacing.xs,
  },
  translatedText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  mediaContainer: {
    marginBottom: spacing.sm,
    borderRadius: borderRadius.sm,
    overflow: 'hidden',
  },
  media: {
    width: '100%',
    height: 200,
    borderRadius: borderRadius.sm,
  },
  noMediaContainer: {
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    borderRadius: borderRadius.sm,
    marginBottom: spacing.sm,
  },
  noMediaText: {
    fontSize: 14,
    color: theme.colors.text,
    opacity: 0.5,
  },
  mediaButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: spacing.sm,
    paddingHorizontal: spacing.sm,
  },
  mediaButton: {
    flex: 1,
    marginHorizontal: spacing.xs,
  },
  saveImageButton: {
    borderColor: theme.colors.primary,
  },
  saveVideoButton: {
    borderColor: theme.colors.primary,
  },
  actionButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  actionButton: {
    flex: 1,
    marginHorizontal: spacing.xs,
    marginVertical: spacing.xs,
    minWidth: 80,
  },
  twitterButton: {
    backgroundColor: '#1DA1F2',
  },
  deleteButton: {
    borderColor: theme.colors.error,
  },
  archiveButton: {
    borderColor: '#9E9E9E',
  },
  fab: {
    position: 'absolute',
    bottom: 16,
    right: 16,
    backgroundColor: theme.colors.primary,
  },
  modalContainer: {
    backgroundColor: 'white',
    padding: spacing.lg,
    margin: spacing.lg,
    borderRadius: borderRadius.md,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: spacing.xs,
  },
  notesInput: {
    marginVertical: spacing.md,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: spacing.md,
  },
});

export default PostsScreen; 