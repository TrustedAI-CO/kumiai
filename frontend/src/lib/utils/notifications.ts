/**
 * Desktop notification utility for PM agent notifications.
 *
 * Provides simple browser desktop notifications when the PM agent
 * calls the notify_user tool.
 */

export interface NotificationOptions {
  title: string;
  message: string;
  project_name?: string;
  priority?: 'low' | 'normal' | 'high';
}

class DesktopNotificationService {
  private permission: NotificationPermission = 'default';

  constructor() {
    if ('Notification' in window) {
      this.permission = Notification.permission;
    }
  }

  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('[Notifications] Browser does not support notifications');
      return false;
    }

    if (this.permission === 'granted') {
      return true;
    }

    if (this.permission === 'denied') {
      console.warn('[Notifications] Notification permission denied');
      return false;
    }

    try {
      this.permission = await Notification.requestPermission();
      return this.permission === 'granted';
    } catch (error) {
      console.error('[Notifications] Failed to request permission:', error);
      return false;
    }
  }

  show(options: NotificationOptions): Notification | null {
    console.log('[Notifications] Attempting to show notification:', {
      title: options.title,
      message: options.message,
      project_name: options.project_name,
      priority: options.priority,
      permission: this.permission,
      isSupported: this.isSupported()
    });

    if (this.permission !== 'granted') {
      console.warn('[Notifications] Cannot show notification - permission:', this.permission);
      return null;
    }

    try {
      // Format: Project: [project name] / Title: [title] / message
      const notificationTitle = 'KumiAI';
      const notificationBody = options.project_name
        ? `Project: ${options.project_name}\nTitle: ${options.title}\n${options.message}`
        : `Title: ${options.title}\n${options.message}`;

      const notification = new Notification(notificationTitle, {
        body: notificationBody,
        icon: '/favicon.ico',
        tag: `pm-notification-${Date.now()}`,
        requireInteraction: options.priority === 'high',
      });

      console.log('[Notifications] ✓ Notification created successfully');

      // Auto-close after duration based on priority
      const duration = options.priority === 'high' ? 10000 : 5000;
      if (options.priority !== 'high') {
        setTimeout(() => {
          console.log('[Notifications] Auto-closing notification');
          notification.close();
        }, duration);
      }

      return notification;
    } catch (error) {
      console.error('[Notifications] ✗ Failed to show notification:', error);
      return null;
    }
  }

  isSupported(): boolean {
    return 'Notification' in window;
  }

  getPermission(): NotificationPermission {
    return this.permission;
  }
}

export const desktopNotifications = new DesktopNotificationService();
