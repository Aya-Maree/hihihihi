import {
  Calendar, Users, DollarSign, MapPin, Utensils,
  Tag, AlertTriangle, CheckCircle, Clock, Baby, UserCheck
} from 'lucide-react'
import clsx from 'clsx'

export default function EventContextPanel({ context }) {
  if (!context) return null

  const fields = [
    { icon: Tag, label: 'Event Type', value: context.event_type, color: 'text-purple-600' },
    { icon: Calendar, label: 'Date', value: context.event_date },
    { icon: Clock, label: 'Time', value: context.event_time },
    {
      icon: Users,
      label: 'Guests',
      value: context.guest_count_confirmed
        ? `${context.guest_count_confirmed} (confirmed)`
        : context.guest_count_estimated
        ? `~${context.guest_count_estimated} (estimated)`
        : null,
    },
    {
      icon: DollarSign,
      label: 'Budget',
      value: context.budget_total
        ? `$${context.budget_total.toFixed(0)} total${context.budget_allocated ? ` · $${context.budget_allocated.toFixed(0)} allocated` : ''}`
        : null,
      color: context.budget_allocated > context.budget_total ? 'text-red-600' : 'text-gray-700',
    },
    { icon: MapPin, label: 'Venue', value: context.venue_type || context.location },
    { icon: Tag, label: 'Theme', value: context.theme },
    {
      icon: Utensils,
      label: 'Dietary',
      value: context.dietary_restrictions?.length
        ? context.dietary_restrictions.join(', ')
        : null,
    },
    {
      icon: Baby,
      label: 'Children',
      value: context.has_children ? 'Yes' : null,
    },
    {
      icon: UserCheck,
      label: 'Elderly guests',
      value: context.has_elderly ? 'Yes' : null,
    },
  ].filter((f) => f.value)

  const hasConflicts = context.detected_conflicts?.length > 0
  const isComplete = fields.length >= 4

  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Your Event
        </h3>
        {isComplete ? (
          <span className="flex items-center gap-1 text-xs text-green-600">
            <CheckCircle className="w-3 h-3" /> Looking good!
          </span>
        ) : (
          <span className="text-xs text-gray-400">Building your plan…</span>
        )}
      </div>

      {fields.length === 0 ? (
        <p className="text-xs text-gray-400 italic">Start chatting and we'll fill this in as you go.</p>
      ) : (
        <div className="space-y-2">
          {fields.map(({ icon: Icon, label, value, color }, i) => (
            <div key={i} className="flex items-start gap-2">
              <Icon className="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
              <div className="min-w-0">
                <span className="text-xs text-gray-500">{label}: </span>
                <span className={clsx('text-xs font-medium capitalize', color || 'text-gray-800')}>
                  {value}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Conflicts */}
      {hasConflicts && (
        <div className="mt-2 pt-2 border-t border-orange-100">
          <div className="flex items-center gap-1 mb-1">
            <AlertTriangle className="w-3.5 h-3.5 text-orange-500" />
            <span className="text-xs font-medium text-orange-700">Heads up</span>
          </div>
          {context.detected_conflicts.map((c, i) => (
            <p key={i} className="text-xs text-orange-600 leading-tight">{c}</p>
          ))}
        </div>
      )}

      {/* Pending tasks count */}
      {context.pending_tasks?.length > 0 && (
        <div className="pt-2 border-t border-gray-100">
          <span className="text-xs text-gray-500">
            {context.pending_tasks.length} things still to sort out
          </span>
        </div>
      )}
    </div>
  )
}
