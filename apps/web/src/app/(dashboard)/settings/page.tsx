'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import { useAPIKeys, useCreateAPIKey, useRevokeAPIKey } from '@/lib/api/hooks';
import { api } from '@/lib/api/client';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/loading';
import { ErrorBanner } from '@/components/ui/error';
import {
  User,
  Key,
  Bell,
  Shield,
  Plus,
  Copy,
  Check,
  Trash2,
  Eye,
  EyeOff,
  AlertTriangle,
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import type { APIKeyInfo, APIResponse } from '@/lib/api/types';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">Manage your account preferences</p>
      </div>

      {/* Profile */}
      <ProfileSection user={user} />

      {/* Security - Change Password */}
      <ChangePasswordSection />

      {/* API Keys */}
      <APIKeysSection />

      {/* Notifications (Placeholder) */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-600/20">
              <Bell className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <CardTitle className="text-white">Notifications</CardTitle>
              <CardDescription className="text-slate-400">
                Alert preferences
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-slate-400 text-sm">
            Notification settings coming soon...
          </p>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="bg-slate-900/50 border-red-900/50">
        <CardHeader>
          <CardTitle className="text-red-400">Danger Zone</CardTitle>
          <CardDescription className="text-slate-400">
            Irreversible actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Delete Account</p>
              <p className="text-sm text-slate-400">
                Permanently delete your account and all data
              </p>
            </div>
            <Button variant="destructive">Delete Account</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ProfileSection({ user }: { user: { email?: string; tier?: string } | null }) {
  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-600/20">
            <User className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <CardTitle className="text-white">Profile</CardTitle>
            <CardDescription className="text-slate-400">
              Your account information
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">Email</label>
          <Input
            value={user?.email || ''}
            disabled
            className="bg-slate-800 border-slate-700 text-white"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">
            Account Tier
          </label>
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-emerald-600/20 text-emerald-400 text-sm capitalize">
              {user?.tier || 'free'}
            </span>
            <Button
              variant="link"
              className="text-emerald-400 hover:text-emerald-300 p-0"
            >
              Upgrade
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ChangePasswordSection() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      await api.put('/auth/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setIsLoading(false);
    }
  };

  // Password strength indicator
  const getPasswordStrength = (password: string) => {
    if (!password) return { label: '', color: '' };
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    if (strength <= 2) return { label: 'Weak', color: 'bg-red-500' };
    if (strength <= 3) return { label: 'Medium', color: 'bg-amber-500' };
    return { label: 'Strong', color: 'bg-emerald-500' };
  };

  const passwordStrength = getPasswordStrength(newPassword);

  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-600/20">
            <Shield className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <CardTitle className="text-white">Change Password</CardTitle>
            <CardDescription className="text-slate-400">
              Update your account password
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}
          {success && (
            <div className="p-3 rounded-md bg-emerald-900/20 border border-emerald-800 text-emerald-400 text-sm flex items-center">
              <Check className="h-4 w-4 mr-2" />
              Password changed successfully
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              Current Password
            </label>
            <div className="relative">
              <Input
                type={showPasswords ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
                onClick={() => setShowPasswords(!showPasswords)}
              >
                {showPasswords ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              New Password
            </label>
            <Input
              type={showPasswords ? 'text' : 'password'}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="bg-slate-800 border-slate-700 text-white"
            />
            {newPassword && (
              <div className="flex items-center space-x-2">
                <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={cn('h-full transition-all', passwordStrength.color)}
                    style={{
                      width:
                        passwordStrength.label === 'Weak'
                          ? '33%'
                          : passwordStrength.label === 'Medium'
                          ? '66%'
                          : '100%',
                    }}
                  />
                </div>
                <span className="text-xs text-slate-400">
                  {passwordStrength.label}
                </span>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              Confirm New Password
            </label>
            <Input
              type={showPasswords ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={cn(
                'bg-slate-800 border-slate-700 text-white',
                confirmPassword &&
                  confirmPassword !== newPassword &&
                  'border-red-500'
              )}
            />
          </div>

          <Button
            type="submit"
            className="bg-emerald-600 hover:bg-emerald-500 text-white"
            disabled={!currentPassword || !newPassword || !confirmPassword}
            isLoading={isLoading}
          >
            Update Password
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function APIKeysSection() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyExpiry, setNewKeyExpiry] = useState('');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState<string | null>(null);

  const { data: apiKeys, isLoading, isError, refetch } = useAPIKeys();
  const createKey = useCreateAPIKey();
  const revokeKey = useRevokeAPIKey();

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName) return;

    try {
      const result = await createKey.mutateAsync({
        name: newKeyName,
        expires_in_days: newKeyExpiry ? parseInt(newKeyExpiry) : undefined,
      });
      setCreatedKey(result.key);
      setNewKeyName('');
      setNewKeyExpiry('');
    } catch (error) {
      console.error('Failed to create API key:', error);
    }
  };

  const handleCopyKey = async () => {
    if (!createdKey) return;
    await navigator.clipboard.writeText(createdKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRevokeKey = async (keyId: string) => {
    try {
      await revokeKey.mutateAsync(keyId);
      setKeyToDelete(null);
    } catch (error) {
      console.error('Failed to revoke key:', error);
    }
  };

  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-600/20">
              <Key className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <CardTitle className="text-white">API Keys</CardTitle>
              <CardDescription className="text-slate-400">
                Manage programmatic access
              </CardDescription>
            </div>
          </div>
          <Button
            onClick={() => setIsCreateModalOpen(true)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white"
            size="sm"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Key
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Created Key Display (shown once) */}
        {createdKey && (
          <div className="mb-4 p-4 rounded-lg bg-emerald-900/20 border border-emerald-800">
            <div className="flex items-center justify-between mb-2">
              <p className="text-emerald-400 font-medium text-sm">
                New API Key Created
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopyKey}
                className="text-emerald-400 hover:text-emerald-300"
              >
                {copied ? (
                  <Check className="h-4 w-4 mr-1" />
                ) : (
                  <Copy className="h-4 w-4 mr-1" />
                )}
                {copied ? 'Copied!' : 'Copy'}
              </Button>
            </div>
            <code className="block p-2 bg-slate-900 rounded text-sm text-white font-mono break-all">
              {createdKey}
            </code>
            <div className="flex items-center mt-2 text-xs text-amber-400">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Copy this key now. You won&apos;t be able to see it again.
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 text-slate-400"
              onClick={() => setCreatedKey(null)}
            >
              Dismiss
            </Button>
          </div>
        )}

        {/* Create Key Form */}
        {isCreateModalOpen && !createdKey && (
          <form onSubmit={handleCreateKey} className="mb-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
            <p className="text-white font-medium mb-3">Create New API Key</p>
            <div className="space-y-3">
              <Input
                placeholder="Key name (e.g., Production)"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
              />
              <Input
                type="number"
                placeholder="Expires in days (optional)"
                value={newKeyExpiry}
                onChange={(e) => setNewKeyExpiry(e.target.value)}
                min={1}
                max={365}
                className="bg-slate-800 border-slate-700 text-white"
              />
              <div className="flex space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  className="border-slate-700 text-slate-300"
                  onClick={() => {
                    setIsCreateModalOpen(false);
                    setNewKeyName('');
                    setNewKeyExpiry('');
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="bg-emerald-600 hover:bg-emerald-500 text-white"
                  disabled={!newKeyName}
                  isLoading={createKey.isPending}
                >
                  Create
                </Button>
              </div>
            </div>
          </form>
        )}

        {/* Keys List */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : isError ? (
          <ErrorBanner message="Failed to load API keys" />
        ) : apiKeys && apiKeys.length > 0 ? (
          <div className="space-y-2">
            {apiKeys.map((key) => (
              <APIKeyRow
                key={key.key_id}
                apiKey={key}
                onRevoke={() => setKeyToDelete(key.key_id)}
                isDeleting={keyToDelete === key.key_id}
                onConfirmRevoke={() => handleRevokeKey(key.key_id)}
                onCancelRevoke={() => setKeyToDelete(null)}
              />
            ))}
          </div>
        ) : (
          <p className="text-slate-500 text-sm text-center py-4">
            No API keys yet. Create one to get started.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function APIKeyRow({
  apiKey,
  onRevoke,
  isDeleting,
  onConfirmRevoke,
  onCancelRevoke,
}: {
  apiKey: APIKeyInfo;
  onRevoke: () => void;
  isDeleting: boolean;
  onConfirmRevoke: () => void;
  onCancelRevoke: () => void;
}) {
  const isExpired = apiKey.expires_at && new Date(apiKey.expires_at) < new Date();

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center">
          <Key className="h-4 w-4 text-slate-400" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <p className="text-white font-medium">{apiKey.name}</p>
            {isExpired && (
              <span className="px-1.5 py-0.5 text-xs rounded bg-red-900/50 text-red-400">
                Expired
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500">
            {apiKey.key_prefix}••••••••
            {apiKey.last_used_at && (
              <> · Last used {new Date(apiKey.last_used_at).toLocaleDateString()}</>
            )}
          </p>
        </div>
      </div>
      <div>
        {isDeleting ? (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-red-400">Revoke?</span>
            <Button
              variant="ghost"
              size="sm"
              className="text-red-400 hover:text-red-300 h-8 px-2"
              onClick={onConfirmRevoke}
            >
              Yes
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 h-8 px-2"
              onClick={onCancelRevoke}
            >
              No
            </Button>
          </div>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-400 hover:text-red-400"
            onClick={onRevoke}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
