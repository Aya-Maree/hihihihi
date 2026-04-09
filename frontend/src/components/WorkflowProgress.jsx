import clsx from 'clsx'
import { Check, Circle, Loader2 } from 'lucide-react'

const STEPS = [
  { id: 'intake', label: 'Intake', desc: 'Collecting event details' },
  { id: 'clarification', label: 'Clarify', desc: 'Resolving ambiguities' },
  { id: 'retrieval', label: 'Retrieve', desc: 'Searching knowledge base' },
  { id: 'conflict_detection', label: 'Check', desc: 'Detecting conflicts' },
  { id: 'planning', label: 'Plan', desc: 'Generating strategy' },
  { id: 'validation', label: 'Validate', desc: 'Reviewing constraints' },
  { id: 'artifact_generation', label: 'Generate', desc: 'Creating documents' },
  { id: 'complete', label: 'Done', desc: 'Plan complete!' },
]

export default function WorkflowProgress({ currentStep }) {
  const currentIdx = STEPS.findIndex((s) => s.id === currentStep)

  return (
    <div className="card p-4">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Planning Workflow
      </h3>
      <div className="space-y-2">
        {STEPS.map((step, i) => {
          const isDone = i < currentIdx
          const isActive = i === currentIdx
          const isPending = i > currentIdx

          return (
            <div key={step.id} className="flex items-center gap-2.5">
              {/* Step icon */}
              <div
                className={clsx(
                  'w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-xs',
                  isDone && 'bg-green-500',
                  isActive && 'bg-purple-600',
                  isPending && 'bg-gray-200'
                )}
              >
                {isDone && <Check className="w-3 h-3 text-white" />}
                {isActive && <Loader2 className="w-3 h-3 text-white animate-spin" />}
                {isPending && <span className="text-gray-400">{i + 1}</span>}
              </div>

              {/* Label */}
              <div>
                <span
                  className={clsx(
                    'text-xs font-medium',
                    isDone && 'text-green-700',
                    isActive && 'text-purple-700',
                    isPending && 'text-gray-400'
                  )}
                >
                  {step.label}
                </span>
                {isActive && (
                  <p className="text-xs text-gray-400">{step.desc}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
