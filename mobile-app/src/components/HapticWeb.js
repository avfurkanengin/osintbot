// Web version of haptic feedback (no-op for browser)
const HapticFeedback = {
  trigger: (type) => {
    // In a real implementation, you could use Web Vibration API
    if (navigator.vibrate) {
      switch (type) {
        case 'impactLight':
          navigator.vibrate(10);
          break;
        case 'impactMedium':
          navigator.vibrate(20);
          break;
        case 'impactHeavy':
          navigator.vibrate(30);
          break;
        default:
          navigator.vibrate(15);
      }
    }
    console.log(`Haptic feedback: ${type}`);
  },
};

export default HapticFeedback; 