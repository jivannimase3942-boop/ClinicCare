import React, { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { authService } from '@/services/auth'
import { useToast } from '@/context/ToastContext'
import { Card, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { User, Mail, Phone, Lock, ShieldCheck } from 'lucide-react'

export const ProfilePage: React.FC = () => {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentPassword || !newPassword) return
    setIsUpdating(true)
    try {
      await authService.changePassword(currentPassword, newPassword)
      showToast('Password updated successfully', 'success')
      setCurrentPassword('')
      setNewPassword('')
    } catch (err: any) {
      showToast(err.message || 'Failed to update password', 'error')
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Patient Profile & Security</h1>
        <p className="text-xs text-slate-500">Manage personal identification, contact details, and account credentials</p>
      </div>

      <Card className="space-y-4">
        <CardTitle>Personal Information</CardTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="Full Name" value={user?.full_name || ''} disabled leftIcon={<User className="w-4 h-4" />} />
          <Input label="Email Address" value={user?.email || ''} disabled leftIcon={<Mail className="w-4 h-4" />} />
          <Input label="Phone Number" value={user?.phone || 'Not provided'} disabled leftIcon={<Phone className="w-4 h-4" />} />
          <Input label="Account Role" value={user?.role || ''} disabled leftIcon={<ShieldCheck className="w-4 h-4" />} />
        </div>
      </Card>

      <Card className="space-y-4">
        <CardTitle>Change Security Password</CardTitle>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <Input
            label="Current Password"
            type="password"
            placeholder="••••••••"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            leftIcon={<Lock className="w-4 h-4" />}
            required
          />
          <Input
            label="New Password"
            type="password"
            placeholder="••••••••"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            leftIcon={<Lock className="w-4 h-4" />}
            required
            minLength={6}
          />
          <Button type="submit" isLoading={isUpdating} disabled={isUpdating}>
            Update Password
          </Button>
        </form>
      </Card>
    </div>
  )
}
