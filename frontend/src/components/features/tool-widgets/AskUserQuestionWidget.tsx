/**
 * AskUserQuestion Widget - interactive questions with multiple choice options
 */

import React, { useState } from 'react';
import { HelpCircle, Check } from 'lucide-react';
import { CollapsibleWidget } from './CollapsibleWidget';
import { WIDGET_HEADER_TEXT_SIZE } from './utils';
import type { ToolWidgetProps } from './types';
import { sendMessage } from '@/lib/services/messageSender';
import { useParams } from 'react-router-dom';

interface QuestionOption {
  label: string;
  description: string;
}

interface Question {
  question: string;
  header: string;
  multiSelect: boolean;
  options: QuestionOption[];
}

interface QuestionData {
  questions: Question[];
}

export const AskUserQuestionWidget: React.FC<ToolWidgetProps> = ({
  toolArgs,
  result,
  isLoading,
}) => {
  const { instanceId = '' } = useParams<{ instanceId: string }>();
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string[]>>({});
  const [otherInputs, setOtherInputs] = useState<Record<number, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Parse questions from toolArgs
  let questionData: QuestionData | null = null;
  try {
    const jsonStr = typeof toolArgs === 'string' ? toolArgs : JSON.stringify(toolArgs);
    const parsed = JSON.parse(jsonStr);
    questionData = parsed.questions ? parsed : { questions: parsed };
  } catch (e) {
    console.error('Failed to parse question data:', e);
  }

  const questions = questionData?.questions || [];
  const hasAnswered = !!result;

  const handleOptionChange = (questionIdx: number, optionLabel: string, isMulti: boolean) => {
    setSelectedAnswers(prev => {
      const current = prev[questionIdx] || [];

      if (isMulti) {
        // Multi-select: toggle option
        if (current.includes(optionLabel)) {
          return { ...prev, [questionIdx]: current.filter(l => l !== optionLabel) };
        } else {
          return { ...prev, [questionIdx]: [...current, optionLabel] };
        }
      } else {
        // Single-select: replace
        return { ...prev, [questionIdx]: [optionLabel] };
      }
    });
  };

  const handleOtherInputChange = (questionIdx: number, value: string) => {
    setOtherInputs(prev => ({ ...prev, [questionIdx]: value }));
  };

  const handleSubmit = async () => {
    // Validate all questions have answers
    for (let i = 0; i < questions.length; i++) {
      const answers = selectedAnswers[i] || [];
      const otherValue = otherInputs[i];

      if (answers.length === 0 && !otherValue) {
        alert(`Please answer question ${i + 1}`);
        return;
      }
    }

    // Build answer message
    const answerLines = questions.map((q, idx) => {
      const answers = selectedAnswers[idx] || [];
      const otherValue = otherInputs[idx];
      const allAnswers = [...answers, otherValue].filter(Boolean);

      return `**${q.header}:** ${allAnswers.join(', ')}`;
    });

    const answerMessage = `My answers:\n\n${answerLines.join('\n')}`;

    setIsSubmitting(true);
    try {
      await sendMessage(instanceId, answerMessage);
    } catch (error) {
      console.error('Failed to send answer:', error);
      alert('Failed to send answer. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const header = (
    <>
      <HelpCircle className="h-3.5 w-3.5 text-primary flex-shrink-0" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>
        {hasAnswered ? 'Question Answered' : 'Question'}
      </span>
      {questions.length > 0 && (
        <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-500 truncate`}>
          {questions[0].question}
        </span>
      )}
    </>
  );

  return (
    <CollapsibleWidget header={header} toolArgs={toolArgs} result={result}>
      <div className="p-4 space-y-4">
        {questions.map((q, qIdx) => (
          <div key={qIdx} className="space-y-3">
            <div>
              <div className="type-body font-medium text-gray-900 mb-1">{q.question}</div>
              {q.multiSelect && (
                <div className="type-caption text-gray-500">Select all that apply</div>
              )}
            </div>

            {/* Options */}
            <div className="space-y-2">
              {q.options.map((opt, optIdx) => {
                const isSelected = (selectedAnswers[qIdx] || []).includes(opt.label);
                const inputType = q.multiSelect ? 'checkbox' : 'radio';
                const inputName = `question-${qIdx}`;

                return (
                  <label
                    key={optIdx}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      isSelected
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    } ${hasAnswered ? 'opacity-60 pointer-events-none' : ''}`}
                  >
                    <input
                      type={inputType}
                      name={inputName}
                      checked={isSelected}
                      onChange={() => handleOptionChange(qIdx, opt.label, q.multiSelect)}
                      disabled={hasAnswered}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="type-body-sm font-medium text-gray-900">{opt.label}</div>
                      <div className="type-caption text-gray-600 mt-0.5">{opt.description}</div>
                    </div>
                  </label>
                );
              })}

              {/* Other option */}
              {!hasAnswered && (
                <div className="flex items-center gap-2">
                  <span className="type-body-sm text-gray-600">Other:</span>
                  <input
                    type="text"
                    value={otherInputs[qIdx] || ''}
                    onChange={(e) => handleOtherInputChange(qIdx, e.target.value)}
                    placeholder="Type your answer..."
                    className="flex-1 px-3 py-2 border border-gray-200 rounded-lg type-body-sm focus:outline-none focus:border-primary"
                  />
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Submit button */}
        {!hasAnswered && !isLoading && (
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full px-4 py-2 bg-primary text-white rounded-lg type-body-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>Submitting...</>
            ) : (
              <>
                <Check className="h-4 w-4" />
                Submit Answers
              </>
            )}
          </button>
        )}

        {/* Answered state */}
        {hasAnswered && (
          <div className="p-3 rounded-lg bg-green-50 border border-green-200 type-body-sm text-green-700 flex items-center gap-2">
            <Check className="h-4 w-4" />
            Answers submitted
          </div>
        )}
      </div>
    </CollapsibleWidget>
  );
};
