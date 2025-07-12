import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Dimensions,
  Alert,
  Share,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Chip,
  SegmentedButtons,
  FAB,
  Portal,
  Modal,
  List,
} from 'react-native-paper';
import {
  LineChart,
  BarChart,
  PieChart,
  ContributionGraph,
} from 'react-native-chart-kit';
import { useApi } from '../context/ApiContext';
import { theme, spacing, borderRadius, shadows } from '../theme';

const { width } = Dimensions.get('window');
const chartConfig = {
  backgroundGradientFrom: '#ffffff',
  backgroundGradientTo: '#ffffff',
  color: (opacity = 1) => `rgba(33, 150, 243, ${opacity})`,
  strokeWidth: 2,
  barPercentage: 0.5,
  useShadowColorFromDataset: false,
};

const AnalyticsScreen: React.FC = () => {
  const { state, fetchAnalytics, fetchStats } = useApi();
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('7');
  const [showExportModal, setShowExportModal] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, [selectedPeriod]);

  const loadAnalytics = async () => {
    await fetchAnalytics(parseInt(selectedPeriod));
    await fetchStats();
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadAnalytics();
    setRefreshing(false);
  };

  const getStatusData = () => {
    if (!state.analytics?.posts_by_status) return [];
    
    const statusColors = {
      pending: '#FF9800',
      posted: '#4CAF50',
      deleted: '#F44336',
      archived: '#9E9E9E',
      rejected: '#FF5722',
    };

    return Object.entries(state.analytics.posts_by_status).map(([status, count]) => ({
      name: status.charAt(0).toUpperCase() + status.slice(1),
      population: count,
      color: statusColors[status as keyof typeof statusColors] || '#2196F3',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    }));
  };

  const getChannelData = () => {
    if (!state.analytics?.posts_by_channel) return { labels: [], datasets: [{ data: [] }] };
    
    const channels = Object.entries(state.analytics.posts_by_channel)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5); // Top 5 channels

    return {
      labels: channels.map(([channel]) => channel.length > 10 ? channel.substring(0, 10) + '...' : channel),
      datasets: [{
        data: channels.map(([,count]) => count),
      }],
    };
  };

  const getDailyData = () => {
    if (!state.analytics?.daily_posts) return { labels: [], datasets: [{ data: [] }] };
    
    const sortedDays = Object.entries(state.analytics.daily_posts)
      .sort(([a], [b]) => new Date(a).getTime() - new Date(b).getTime());

    // Ensure we have at least one data point to prevent chart errors
    if (sortedDays.length === 0) {
      return { labels: ['No Data'], datasets: [{ data: [0] }] };
    }

    return {
      labels: sortedDays.map(([date]) => {
        const d = new Date(date);
        return `${d.getMonth() + 1}/${d.getDate()}`;
      }),
      datasets: [{
        data: sortedDays.map(([,count]) => Math.max(count, 0)), // Ensure non-negative values
        color: (opacity = 1) => `rgba(33, 150, 243, ${opacity})`,
        strokeWidth: 2,
      }],
    };
  };

  const periodOptions = [
    { value: '7', label: '7 days' },
    { value: '14', label: '14 days' },
    { value: '30', label: '30 days' },
  ];

  const exportData = async (format: 'json' | 'csv' | 'summary') => {
    try {
      let content = '';
      const timestamp = new Date().toISOString().split('T')[0];
      
      if (format === 'json') {
        content = JSON.stringify({
          exported_at: new Date().toISOString(),
          period: selectedPeriod,
          stats: state.stats,
          analytics: state.analytics,
        }, null, 2);
      } else if (format === 'csv') {
        // Create CSV for daily posts
        const dailyData = state.analytics?.daily_posts || {};
        content = 'Date,Posts\n';
        Object.entries(dailyData).forEach(([date, count]) => {
          content += `${date},${count}\n`;
        });
      } else if (format === 'summary') {
        content = `OSINT Bot Analytics Summary - ${timestamp}\n`;
        content += `Period: ${selectedPeriod} days\n\n`;
        content += `Total Posts: ${state.stats?.total_posts || 0}\n`;
        content += `Pending Posts: ${state.stats?.pending_posts || 0}\n`;
        content += `Post Rate: ${state.stats?.post_rate || 0}%\n`;
        content += `Average Quality: ${state.analytics?.quality_metrics?.avg_quality ? (state.analytics.quality_metrics.avg_quality * 100).toFixed(1) + '%' : '0%'}\n`;
        content += `Average Bias: ${state.analytics?.quality_metrics?.avg_bias ? (state.analytics.quality_metrics.avg_bias * 100).toFixed(1) + '%' : '0%'}\n\n`;
        
        if (state.analytics?.posts_by_status) {
          content += 'Posts by Status:\n';
          Object.entries(state.analytics.posts_by_status).forEach(([status, count]) => {
            content += `  ${status}: ${count}\n`;
          });
        }
      }

      await Share.share({
        message: content,
        title: `OSINT Analytics Export - ${timestamp}`,
      });
      
      setShowExportModal(false);
    } catch (error) {
      console.error('Export error:', error);
      Alert.alert('Export Error', 'Failed to export data. Please try again.');
    }
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          colors={[theme.colors.primary]}
        />
      }
    >
      <View style={styles.periodSelector}>
        <SegmentedButtons
          value={selectedPeriod}
          onValueChange={setSelectedPeriod}
          buttons={periodOptions}
        />
      </View>

      {/* Stats Cards */}
      <View style={styles.statsGrid}>
        <Card style={styles.statCard}>
          <Card.Content>
            <Title style={styles.statNumber}>
              {state.stats?.total_posts || 0}
            </Title>
            <Paragraph style={styles.statLabel}>Total Posts</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Title style={styles.statNumber}>
              {state.stats?.pending_posts || 0}
            </Title>
            <Paragraph style={styles.statLabel}>Pending</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Title style={[styles.statNumber, { color: theme.colors.success }]}>
              {state.stats?.post_rate || 0}%
            </Title>
            <Paragraph style={styles.statLabel}>Post Rate</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Title style={[styles.statNumber, { color: theme.colors.warning }]}>
              {state.analytics?.quality_metrics?.avg_quality 
                ? (state.analytics.quality_metrics.avg_quality * 100).toFixed(1) + '%'
                : '0%'
              }
            </Title>
            <Paragraph style={styles.statLabel}>Avg Quality</Paragraph>
          </Card.Content>
        </Card>
      </View>

      {/* Daily Posts Chart */}
      <Card style={styles.chartCard}>
        <Card.Content>
          <Title style={styles.chartTitle}>Daily Posts</Title>
          {state.loading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Loading chart data...</Text>
            </View>
          ) : getDailyData().labels.length > 0 && getDailyData().labels[0] !== 'No Data' ? (
            <LineChart
              data={getDailyData()}
              width={width - 60}
              height={220}
              chartConfig={chartConfig}
              bezier
              style={styles.chart}
              onDataPointClick={(data) => {
                // Optional: Handle data point clicks
                console.log('Data point clicked:', data);
              }}
            />
          ) : (
            <View style={styles.noDataContainer}>
              <Text style={styles.noDataText}>No data available for the selected period</Text>
              <Button
                mode="outlined"
                onPress={onRefresh}
                style={styles.retryButton}
              >
                Retry
              </Button>
            </View>
          )}
        </Card.Content>
      </Card>

      {/* Status Distribution */}
      <Card style={styles.chartCard}>
        <Card.Content>
          <Title style={styles.chartTitle}>Status Distribution</Title>
          {getStatusData().length > 0 ? (
            <PieChart
              data={getStatusData()}
              width={width - 60}
              height={220}
              chartConfig={chartConfig}
              accessor="population"
              backgroundColor="transparent"
              paddingLeft="15"
              style={styles.chart}
            />
          ) : (
            <View style={styles.noDataContainer}>
              <Text style={styles.noDataText}>No data available</Text>
            </View>
          )}
        </Card.Content>
      </Card>

      {/* Channel Performance */}
      <Card style={styles.chartCard}>
        <Card.Content>
          <Title style={styles.chartTitle}>Top Channels</Title>
          {getChannelData().labels.length > 0 ? (
            <BarChart
              data={getChannelData()}
              width={width - 60}
              height={220}
              chartConfig={chartConfig}
              style={styles.chart}
              showValuesOnTopOfBars
            />
          ) : (
            <View style={styles.noDataContainer}>
              <Text style={styles.noDataText}>No data available</Text>
            </View>
          )}
        </Card.Content>
      </Card>

      {/* Quality Metrics */}
      <Card style={styles.chartCard}>
        <Card.Content>
          <Title style={styles.chartTitle}>Quality Metrics</Title>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Average Quality</Text>
              <Text style={[styles.metricValue, { color: theme.colors.success }]}>
                {state.analytics?.quality_metrics?.avg_quality 
                  ? (state.analytics.quality_metrics.avg_quality * 100).toFixed(1) + '%'
                  : '0%'
                }
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Average Bias</Text>
              <Text style={[styles.metricValue, { color: theme.colors.warning }]}>
                {state.analytics?.quality_metrics?.avg_bias 
                  ? (state.analytics.quality_metrics.avg_bias * 100).toFixed(1) + '%'
                  : '0%'
                }
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Total Processed</Text>
              <Text style={styles.metricValue}>
                {state.analytics?.quality_metrics?.total_posts || 0}
              </Text>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* User Actions */}
      {state.analytics?.user_actions && Object.keys(state.analytics.user_actions).length > 0 && (
        <Card style={styles.chartCard}>
          <Card.Content>
            <Title style={styles.chartTitle}>User Actions</Title>
            <View style={styles.actionsContainer}>
              {Object.entries(state.analytics.user_actions).map(([action, count]) => (
                <Chip
                  key={action}
                  style={styles.actionChip}
                  textStyle={styles.actionChipText}
                >
                  {action}: {count}
                </Chip>
              ))}
            </View>
          </Card.Content>
        </Card>
      )}

      <FAB
        icon="download"
        style={styles.exportFab}
        onPress={() => setShowExportModal(true)}
        label="Export"
      />

      <Portal>
        <Modal
          visible={showExportModal}
          onDismiss={() => setShowExportModal(false)}
          contentContainerStyle={styles.exportModal}
        >
          <Title style={styles.modalTitle}>Export Analytics Data</Title>
          <Text style={styles.modalDescription}>
            Choose the format for exporting your analytics data:
          </Text>
          
          <List.Item
            title="JSON Format"
            description="Complete data in JSON format"
            left={(props) => <List.Icon {...props} icon="code-json" />}
            onPress={() => exportData('json')}
            style={styles.exportOption}
          />
          
          <List.Item
            title="CSV Format"
            description="Daily posts data for spreadsheets"
            left={(props) => <List.Icon {...props} icon="table" />}
            onPress={() => exportData('csv')}
            style={styles.exportOption}
          />
          
          <List.Item
            title="Summary Report"
            description="Human-readable summary"
            left={(props) => <List.Icon {...props} icon="file-document" />}
            onPress={() => exportData('summary')}
            style={styles.exportOption}
          />
          
          <Button
            mode="outlined"
            onPress={() => setShowExportModal(false)}
            style={styles.cancelButton}
          >
            Cancel
          </Button>
        </Modal>
      </Portal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  periodSelector: {
    padding: spacing.md,
    backgroundColor: theme.colors.surface,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: spacing.md,
    gap: spacing.sm,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    ...shadows.small,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.primary,
    textAlign: 'center',
  },
  statLabel: {
    fontSize: 12,
    textAlign: 'center',
    opacity: 0.7,
  },
  chartCard: {
    margin: spacing.md,
    ...shadows.medium,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: spacing.md,
    color: theme.colors.text,
  },
  chart: {
    marginVertical: spacing.sm,
    borderRadius: borderRadius.md,
  },
  noDataContainer: {
    height: 220,
    justifyContent: 'center',
    alignItems: 'center',
  },
  noDataText: {
    fontSize: 16,
    color: theme.colors.text,
    opacity: 0.5,
    marginBottom: spacing.md,
  },
  loadingContainer: {
    height: 220,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: theme.colors.text,
    opacity: 0.6,
  },
  retryButton: {
    marginTop: spacing.sm,
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: spacing.md,
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: theme.colors.text,
    opacity: 0.7,
    marginBottom: spacing.xs,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  actionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  actionChip: {
    backgroundColor: theme.colors.primary,
  },
  actionChipText: {
    color: 'white',
    fontSize: 12,
  },
  exportFab: {
    position: 'absolute',
    bottom: 16,
    right: 16,
    backgroundColor: theme.colors.primary,
  },
  exportModal: {
    backgroundColor: 'white',
    margin: spacing.lg,
    padding: spacing.lg,
    borderRadius: borderRadius.md,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: spacing.sm,
    color: theme.colors.text,
  },
  modalDescription: {
    fontSize: 14,
    color: theme.colors.text,
    opacity: 0.7,
    marginBottom: spacing.lg,
  },
  exportOption: {
    marginBottom: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  cancelButton: {
    marginTop: spacing.md,
    alignSelf: 'center',
  },
});

export default AnalyticsScreen; 