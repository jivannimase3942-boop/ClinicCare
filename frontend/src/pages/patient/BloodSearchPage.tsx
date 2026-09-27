import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bloodApi } from '@/services/blood'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import {
  Droplet,
  Search,
  Building,
  PhoneCall,
  MapPin,
  Clock,
  ShieldCheck,
  Activity,
  HeartHandshake,
  PlusCircle,
  ClipboardList,
  CheckCircle2,
} from 'lucide-react'

const BLOOD_GROUPS = ['ALL', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const FORM_BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

export const BloodSearchPage: React.FC = () => {
  const { user } = useAuth()
  const { showToast } = useToast()
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState<'search' | 'request' | 'my-requests'>('search')
  const [selectedGroup, setSelectedGroup] = useState<string>('ALL')
  const [cityFilter, setCityFilter] = useState<string>('')

  // Form states for Request Blood
  const [patientName, setPatientName] = useState(user?.full_name || '')
  const [bloodGroup, setBloodGroup] = useState('O+')
  const [unitsRequired, setUnitsRequired] = useState(1)
  const [hospitalClinic, setHospitalClinic] = useState('ClinicCare Multispeciality Hospital')
  const [location, setLocation] = useState('')
  const [contactPhone, setContactPhone] = useState(user?.phone || '')
  const [urgency, setUrgency] = useState<'normal' | 'urgent' | 'critical'>('urgent')
  const [additionalInfo, setAdditionalInfo] = useState('')

  const { data: searchData, isLoading: searchLoading } = useQuery({
    queryKey: ['blood-search', selectedGroup, cityFilter],
    queryFn: () =>
      bloodApi.searchBlood({
        blood_group: selectedGroup === 'ALL' ? undefined : selectedGroup,
        city: cityFilter || undefined,
      }),
  })

  const { data: banksData, isLoading: banksLoading } = useQuery({
    queryKey: ['blood-banks'],
    queryFn: () => bloodApi.getBanks(),
  })

  const { data: requestsData } = useQuery({
    queryKey: ['my-blood-requests'],
    queryFn: () => bloodApi.getBloodRequests({ patient_id: user?.patient_profile?.id }),
  })

  const inventoryResults = searchData?.data || []
  const bloodBanks = banksData?.data || []
  const myRequests = requestsData?.data || []

  const createRequestMutation = useMutation({
    mutationFn: bloodApi.createBloodRequest,
    onSuccess: (data) => {
      showToast('success', `Blood request submitted! Request ID: #${data.data.id.slice(0, 8)}`)
      queryClient.invalidateQueries({ queryKey: ['my-blood-requests'] })
      setLocation('')
      setAdditionalInfo('')
      setActiveTab('my-requests')
    },
    onError: (err: any) => {
      showToast('error', err.response?.data?.message || 'Failed to submit blood request')
    },
  })

  const handleRequestSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!patientName.trim() || !contactPhone.trim() || !location.trim() || !hospitalClinic.trim()) {
      showToast('error', 'Please fill in all required fields')
      return
    }

    createRequestMutation.mutate({
      patient_name: patientName,
      blood_group: bloodGroup,
      units_required: Number(unitsRequired),
      hospital_clinic_name: hospitalClinic,
      location,
      contact_phone: contactPhone,
      urgency,
      additional_info: additionalInfo || undefined,
      patient_id: user?.patient_profile?.id,
    })
  }

  const getStockBadge = (status: string, units: number) => {
    if (units === 0 || status === 'critical_need') {
      return <Badge variant="danger">Critical Need (0 units)</Badge>
    }
    if (units < 5 || status === 'low_stock') {
      return <Badge variant="warning">Low Stock ({units} units)</Badge>
    }
    return <Badge variant="success">Available ({units} units)</Badge>
  }

  const getRequestStatusBadge = (status: string) => {
    switch (status) {
      case 'searching':
        return <Badge variant="warning">Searching</Badge>
      case 'match_found':
        return <Badge variant="primary">Match Found</Badge>
      case 'fulfilled':
        return <Badge variant="success">Fulfilled</Badge>
      case 'cancelled':
        return <Badge variant="danger">Cancelled</Badge>
      default:
        return <Badge variant="neutral">Submitted</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-rose-600 to-pink-600 rounded-2xl p-6 text-white shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center shrink-0 border border-white/20">
            <Droplet className="w-7 h-7 text-white fill-white" />
          </div>
          <div>
            <h2 className="text-xl font-black tracking-tight">Blood Group Search & Blood Bank Directory</h2>
            <p className="text-xs text-rose-100 mt-0.5">
              Live inventory lookup across verified hospital blood banks and regional transfusion centers.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="neutral" className="bg-white/20 text-white border-0 px-3 py-1.5 font-bold">
            <ShieldCheck className="w-3.5 h-3.5 mr-1 text-teal-300 inline" /> 100% Tested & Verified
          </Badge>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('search')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'search'
              ? 'bg-rose-600 text-white shadow-md shadow-rose-200'
              : 'bg-white text-slate-700 hover:bg-slate-100'
          }`}
        >
          <Search className="w-3.5 h-3.5 inline mr-1.5" />
          Inventory Search & Banks
        </button>
        <button
          onClick={() => setActiveTab('request')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'request'
              ? 'bg-rose-600 text-white shadow-md shadow-rose-200'
              : 'bg-white text-slate-700 hover:bg-slate-100'
          }`}
        >
          <PlusCircle className="w-3.5 h-3.5 inline mr-1.5" />
          Request Blood
        </button>
        <button
          onClick={() => setActiveTab('my-requests')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'my-requests'
              ? 'bg-rose-600 text-white shadow-md shadow-rose-200'
              : 'bg-white text-slate-700 hover:bg-slate-100'
          }`}
        >
          <ClipboardList className="w-3.5 h-3.5 inline mr-1.5" />
          My Blood Requests ({myRequests.length})
        </button>
      </div>

      {activeTab === 'search' && (
        <div className="space-y-6">

      {/* Filter Section */}
      <Card>
        <CardContent className="p-5 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                Select Blood Group Requirement:
              </p>
              <div className="flex flex-wrap gap-2">
                {BLOOD_GROUPS.map((bg) => (
                  <button
                    key={bg}
                    onClick={() => setSelectedGroup(bg)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm ${
                      selectedGroup === bg
                        ? 'bg-rose-600 text-white shadow-rose-200 scale-105'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {bg === 'ALL' ? 'All Blood Groups' : bg}
                  </button>
                ))}
              </div>
            </div>

            <div className="w-full md:w-64">
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                Filter by City / Region:
              </label>
              <div className="relative">
                <Input
                  value={cityFilter}
                  onChange={(e) => setCityFilter(e.target.value)}
                  placeholder="e.g. Metropolis..."
                  className="pl-9 h-9 text-xs"
                />
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Available Blood Units Grid */}
      <div>
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4 text-rose-600" />
          Available Blood Units & Stocks ({inventoryResults.length} records found)
        </h3>

        {inventoryResults.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Droplet className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-bold text-slate-700">No matching blood inventory records</p>
              <p className="text-xs text-slate-500 mt-1">Try selecting another blood group or clearing the city filter.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {inventoryResults.map((item, idx) => (
              <Card key={`${item.blood_bank_id}-${item.blood_group}-${idx}`} className="border-slate-200 hover:border-rose-300 transition">
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="w-11 h-11 rounded-xl bg-rose-50 text-rose-700 flex items-center justify-center font-black text-lg border border-rose-100">
                      {item.blood_group}
                    </span>
                    {getStockBadge(item.status, item.units_available)}
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-900 line-clamp-1">{item.blood_bank_name}</h4>
                    <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      {item.city}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-[11px] text-slate-400">24/7 Transfusion</span>
                    <a
                      href={`tel:${item.phone}`}
                      className="inline-flex items-center gap-1 text-xs font-bold text-rose-600 hover:underline"
                    >
                      <PhoneCall className="w-3.5 h-3.5" /> Call Bank
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Blood Banks Directory */}
      <div className="mt-8">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Building className="w-4 h-4 text-sky-600" />
          Verified Blood Banks & Component Centers
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {bloodBanks.map((bank) => (
            <Card key={bank.id} className="border-slate-200">
              <CardContent className="p-5 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-base font-bold text-slate-900">{bank.name}</h4>
                    <Badge variant="success" className="shrink-0">Verified Center</Badge>
                  </div>
                  <p className="text-xs text-slate-600 flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-slate-400 shrink-0" /> {bank.address}, {bank.city}
                  </p>
                  <p className="text-xs text-slate-600 flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-slate-400 shrink-0" /> {bank.operating_hours}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-700">{bank.phone}</span>
                  <a
                    href={`tel:${bank.phone}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 font-bold text-xs transition"
                  >
                    <PhoneCall className="w-3.5 h-3.5" /> Direct Line
                  </a>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )}

  {activeTab === 'request' && (
    <Card className="max-w-2xl mx-auto border-slate-200">
      <CardHeader className="p-5 pb-3">
        <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
          <PlusCircle className="w-5 h-5 text-rose-600" />
          Submit Blood Requirement Request
        </CardTitle>
      </CardHeader>
      <CardContent className="p-5 pt-0">
        <form onSubmit={handleRequestSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Patient Name *</label>
              <Input
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                placeholder="Enter patient full name"
                required
                className="text-xs h-9"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Contact Phone *</label>
              <Input
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="e.g. +1 (800) 555-0199"
                required
                className="text-xs h-9"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Blood Group *</label>
              <select
                value={bloodGroup}
                onChange={(e) => setBloodGroup(e.target.value)}
                className="w-full h-9 rounded-xl border border-slate-200 bg-white px-3 text-xs font-bold text-slate-800 focus:border-rose-500 focus:outline-none"
              >
                {FORM_BLOOD_GROUPS.map((bg) => (
                  <option key={bg} value={bg}>
                    {bg}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Units Required *</label>
              <Input
                type="number"
                min={1}
                max={20}
                value={unitsRequired}
                onChange={(e) => setUnitsRequired(Number(e.target.value))}
                required
                className="text-xs h-9"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Urgency Level</label>
              <select
                value={urgency}
                onChange={(e: any) => setUrgency(e.target.value)}
                className="w-full h-9 rounded-xl border border-slate-200 bg-white px-3 text-xs font-bold text-slate-800 focus:border-rose-500 focus:outline-none"
              >
                <option value="normal">Normal</option>
                <option value="urgent">Urgent</option>
                <option value="critical">Critical (Immediate)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Hospital / Clinic Name *</label>
              <Input
                value={hospitalClinic}
                onChange={(e) => setHospitalClinic(e.target.value)}
                placeholder="e.g. ClinicCare Main Hospital"
                required
                className="text-xs h-9"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Ward / Location *</label>
              <Input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. ICU Ward 3, Bed 12"
                required
                className="text-xs h-9"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Additional Information / Medical Case</label>
            <textarea
              rows={3}
              value={additionalInfo}
              onChange={(e) => setAdditionalInfo(e.target.value)}
              placeholder="Doctor recommendation, surgery schedule, antibody details..."
              className="w-full rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-800 focus:border-rose-500 focus:outline-none"
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold h-10 shadow-lg shadow-rose-600/20"
            isLoading={createRequestMutation.isPending}
          >
            Submit Blood Requirement Request
          </Button>
        </form>
      </CardContent>
    </Card>
  )}

  {activeTab === 'my-requests' && (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-rose-600" />
          My Blood Requirement Requests ({myRequests.length})
        </h3>
        <Button size="sm" variant="outline" onClick={() => setActiveTab('request')}>
          <PlusCircle className="w-3.5 h-3.5 mr-1" /> New Request
        </Button>
      </div>

      {myRequests.length === 0 ? (
        <Card className="text-center py-10 border-slate-200">
          <CardContent>
            <ClipboardList className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-bold text-slate-700">No blood requests submitted yet</p>
            <p className="text-xs text-slate-500 mt-1">Submit a blood requirement request above to track matching status.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {myRequests.map((req) => (
            <Card key={req.id} className="border-slate-200">
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-9 h-9 rounded-lg bg-rose-50 text-rose-700 flex items-center justify-center font-black text-sm border border-rose-100">
                      {req.blood_group}
                    </span>
                    <div>
                      <p className="text-xs font-mono font-bold text-slate-500">#{req.id.slice(0, 8)}</p>
                      <p className="text-sm font-bold text-slate-900">{req.patient_name}</p>
                    </div>
                  </div>
                  {getRequestStatusBadge(req.status)}
                </div>

                <div className="text-xs text-slate-600 space-y-1 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  <p><span className="font-semibold text-slate-700">Units:</span> {req.units_required} unit(s)</p>
                  <p><span className="font-semibold text-slate-700">Facility:</span> {req.hospital_clinic_name} ({req.location})</p>
                  <p><span className="font-semibold text-slate-700">Urgency:</span> <span className="font-bold text-rose-600 uppercase">{req.urgency}</span></p>
                  {req.matched_bank_name && (
                    <p className="text-teal-700 font-bold flex items-center gap-1 mt-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" /> Matched: {req.matched_bank_name}
                    </p>
                  )}
                  {req.admin_notes && (
                    <p className="text-slate-500 italic mt-1">Note: {req.admin_notes}</p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )}
</div>
)
}

