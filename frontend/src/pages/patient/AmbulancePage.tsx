import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ambulanceApi } from '@/services/ambulances'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Siren, PhoneCall, MapPin, Clock, Send, Truck, Activity } from 'lucide-react'

export const AmbulancePage: React.FC = () => {
  const { user } = useAuth()
  const { showToast } = useToast()
  const queryClient = useQueryClient()

  const [pickupAddress, setPickupAddress] = useState('')
  const [destination, setDestination] = useState('ClinicCare Multispeciality Hospital')
  const [priority, setPriority] = useState<'high' | 'critical' | 'medium'>('critical')
  const [notes, setNotes] = useState('')
  const [callerName, setCallerName] = useState(user?.full_name || '')
  const [callerPhone, setCallerPhone] = useState(user?.phone || '')

  const { data: fleetData } = useQuery({
    queryKey: ['ambulances-fleet'],
    queryFn: () => ambulanceApi.getAmbulances(),
  })

  const { data: requestsData } = useQuery({
    queryKey: ['my-ambulance-requests'],
    queryFn: () => ambulanceApi.getRequests({ patient_id: user?.patient_profile?.id }),
  })

  const ambulances = fleetData?.data || []
  const requests = requestsData?.data || []
  const availableCount = ambulances.filter((a) => a.status === 'available').length

  const requestMutation = useMutation({
    mutationFn: ambulanceApi.requestAmbulance,
    onSuccess: () => {
      showToast('success', 'Ambulance dispatch request submitted successfully!')
      queryClient.invalidateQueries({ queryKey: ['my-ambulance-requests'] })
      queryClient.invalidateQueries({ queryKey: ['ambulances-fleet'] })
      setPickupAddress('')
      setNotes('')
    },
    onError: (err: any) => {
      showToast('error', err.response?.data?.message || 'Failed to submit ambulance request')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!pickupAddress.trim() || !callerPhone.trim() || !callerName.trim()) {
      showToast('error', 'Please complete pickup location, caller name, and contact phone number')
      return
    }

    requestMutation.mutate({
      requester_name: callerName,
      requester_phone: callerPhone,
      pickup_address: pickupAddress,
      destination_facility: destination,
      emergency_priority: priority,
      notes: notes || undefined,
      patient_id: user?.patient_profile?.id,
    })
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'assigned':
        return <Badge variant="warning">Assigned</Badge>
      case 'en_route':
        return <Badge variant="primary">En Route</Badge>
      case 'arrived':
        return <Badge variant="success">Arrived</Badge>
      case 'completed':
        return <Badge variant="success">Completed</Badge>
      case 'cancelled':
        return <Badge variant="danger">Cancelled</Badge>
      default:
        return <Badge variant="neutral">Requested</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-rose-600 to-red-600 rounded-2xl p-5 text-white shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center shrink-0 border border-white/20">
            <Siren className="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-black tracking-tight">Emergency Ambulance Coordination</h2>
            <p className="text-xs text-rose-100 mt-0.5 max-w-xl">
              For critical emergencies, dial 911 / 108 immediately.
              This portal coordinates rapid simulated emergency dispatch with hospital base stations.
            </p>
          </div>
        </div>
        <a
          href="tel:911"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white text-rose-700 font-bold text-sm shadow-md hover:bg-rose-50 transition shrink-0"
        >
          <PhoneCall className="w-4 h-4" /> Emergency Hotline
        </a>
      </div>

      {/* Fleet Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-slate-200">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500">Fleet Availability</p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                {availableCount} <span className="text-sm font-medium text-slate-500">/ {ambulances.length} Online</span>
              </h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
              <Truck className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500">Estimated Response</p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">3-7 Min</h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500">Triage Priority</p>
              <h3 className="text-2xl font-black text-rose-600 mt-1">Critical (ALS)</h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Request Form */}
        <div className="lg:col-span-6">
          <Card>
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-base flex items-center gap-2">
                <Siren className="w-5 h-5 text-rose-600" />
                Dispatch Ambulance to Location
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Caller / Patient Name *
                    </label>
                    <Input
                      value={callerName}
                      onChange={(e) => setCallerName(e.target.value)}
                      placeholder="e.g. John Doe"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Contact Phone *
                    </label>
                    <Input
                      value={callerPhone}
                      onChange={(e) => setCallerPhone(e.target.value)}
                      placeholder="e.g. +1 555-0199"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Pickup Address & Landmarks *
                  </label>
                  <div className="relative">
                    <Input
                      value={pickupAddress}
                      onChange={(e) => setPickupAddress(e.target.value)}
                      placeholder="Street address, building, floor, nearby landmark..."
                      required
                      className="pl-9"
                    />
                    <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Destination Hospital
                    </label>
                    <Input
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      placeholder="ClinicCare Multispeciality Hospital"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Emergency Priority Level
                    </label>
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value as any)}
                      className="w-full h-10 px-3 rounded-xl border border-slate-200 text-sm font-medium focus:ring-2 focus:ring-rose-500 bg-white"
                    >
                      <option value="critical">Critical (Immediate ALS / Trauma)</option>
                      <option value="high">High (Acute Condition)</option>
                      <option value="medium">Medium (Stable Transfer)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Clinical Symptoms / Notes (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="e.g., Shortness of breath, chest discomfort..."
                    className="w-full p-3 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-rose-500 bg-white"
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold py-3 shadow-md shadow-rose-600/20"
                  isLoading={requestMutation.isPending}
                  leftIcon={<Send className="w-4 h-4" />}
                >
                  Confirm & Dispatch Ambulance
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Live Active Requests */}
        <div className="lg:col-span-6 space-y-4">
          <Card>
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="w-5 h-5 text-sky-600" />
                Active Dispatch Status & Tracking
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              {requests.length === 0 ? (
                <div className="text-center py-10">
                  <Truck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-sm font-bold text-slate-700">No active ambulance requests</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Dispatched ambulance details, driver contact, and status will appear here.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {requests.map((req) => (
                    <div
                      key={req.id}
                      className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-slate-500">
                            #{req.id.slice(0, 8)}
                          </span>
                          <span className="text-xs font-bold text-slate-900">
                            {req.requester_name}
                          </span>
                        </div>
                        {getStatusBadge(req.status)}
                      </div>

                      <div className="text-xs text-slate-600 space-y-1">
                        <p className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                          <span className="font-semibold">Pickup:</span> {req.pickup_address}
                        </p>
                        <p className="flex items-center gap-1.5">
                          <Truck className="w-3.5 h-3.5 text-sky-500 shrink-0" />
                          <span className="font-semibold">Destination:</span> {req.destination_facility}
                        </p>
                        {req.ambulance_vehicle_number && (
                          <div className="mt-2 pt-2 border-t border-slate-200 flex items-center justify-between text-xs">
                            <span className="font-bold text-slate-900">
                              Vehicle: {req.ambulance_vehicle_number} ({req.ambulance_model})
                            </span>
                            {req.driver_phone && (
                              <a
                                href={`tel:${req.driver_phone}`}
                                className="text-sky-600 font-bold hover:underline flex items-center gap-1"
                              >
                                <PhoneCall className="w-3 h-3" /> {req.driver_name || 'Driver'}
                              </a>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
