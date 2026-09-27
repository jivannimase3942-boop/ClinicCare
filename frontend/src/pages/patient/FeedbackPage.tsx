import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { feedbackService } from '@/services/feedback'
import { useToast } from '@/context/ToastContext'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Star } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export const FeedbackPage: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')

  const { data: feedbacks = [], isLoading } = useQuery({
    queryKey: ['patient-feedback'],
    queryFn: () => feedbackService.getMyFeedback(),
  })

  const submitMutation = useMutation({
    mutationFn: () => feedbackService.createFeedback({ rating, comment }),
    onSuccess: () => {
      showToast('Thank you for your valuable feedback!', 'success')
      setComment('')
      setRating(5)
      queryClient.invalidateQueries({ queryKey: ['patient-feedback'] })
    },
    onError: (err: any) => showToast(err.message || 'Submission failed', 'error'),
  })

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Patient Experience & Feedback</h1>
        <p className="text-xs text-slate-500">Rate your clinical experience and help us elevate healthcare services</p>
      </div>

      <Card className="p-6 space-y-4">
        <CardTitle>Submit New Review</CardTitle>
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2">Overall Rating</label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                type="button"
                key={star}
                onClick={() => setRating(star)}
                className="p-1 hover:scale-110 transition"
              >
                <Star
                  className={`w-8 h-8 ${
                    rating >= star ? 'text-amber-400 fill-amber-400' : 'text-slate-300'
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Your Comments & Suggestions</label>
          <textarea
            rows={4}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Tell us about the doctor's consultation, hospital staff, triage speed..."
            className="w-full bg-slate-50 border rounded-xl p-3 text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none"
          />
        </div>

        <Button
          onClick={() => submitMutation.mutate()}
          isLoading={submitMutation.isPending}
          disabled={submitMutation.isPending}
        >
          Submit Feedback
        </Button>
      </Card>

      <Card className="space-y-4">
        <CardTitle>My Past Reviews</CardTitle>
        {isLoading ? (
          <p className="text-xs text-slate-400">Loading reviews...</p>
        ) : feedbacks.length === 0 ? (
          <p className="text-xs text-slate-500 py-4">You haven't submitted any feedback yet.</p>
        ) : (
          <div className="space-y-3">
            {feedbacks.map((f) => (
              <div key={f.id} className="p-3 bg-slate-50 rounded-xl border space-y-1.5 text-xs">
                <div className="flex justify-between items-center">
                  <div className="flex text-amber-400">
                    {Array.from({ length: f.rating }).map((_, i) => (
                      <Star key={i} className="w-3.5 h-3.5 fill-amber-400" />
                    ))}
                  </div>
                  <span className="text-slate-400">{formatDate(f.created_at)}</span>
                </div>
                {f.comment && <p className="text-slate-700">{f.comment}</p>}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
