/**
 * AskUserQuestion Widget - interactive questions with multiple choice options
 */

import React, { useState } from 'react';
import { HelpCircle, Check } from 'lucide-react';
import { CollapsibleWidget } from './CollapsibleWidget';
import { WIDGET_HEADER_TEXT_SIZE } from './utils';
import type { ToolWidgetProps } from './types';
import { sendMessage } from '@/lib/services/messageSender';

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
  sessionId,
  isLatestMessage,
}) => {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string[]>>({});
  const [otherInputs, setOtherInputs] = useState<Record<number, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [validationError, setValidationError] = useState<string | null>(null);

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

  // Sanitize user input to prevent XSS
  const sanitizeInput = (input: string): string => {
    return input
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  };

  const handleSubmit = async () => {
    setValidationError(null);

    // Validate all questions have answers
    for (let i = 0; i < questions.length; i++) {
      const answers = selectedAnswers[i] || [];
      const otherValue = otherInputs[i]?.trim();

      if (answers.length === 0 && !otherValue) {
        setValidationError(`Please answer question ${i + 1}`);
        return;
      }
    }

    // Build answer message with proper markdown formatting
    const answerLines = questions.map((q, idx) => {
      const answers = selectedAnswers[idx] || [];
      const otherValue = otherInputs[idx]?.trim();
      // Sanitize user input from "Other" field
      const sanitizedOther = otherValue ? sanitizeInput(otherValue) : null;
      const allAnswers = [...answers, sanitizedOther].filter(Boolean);

      // Format as bullet points if multiple answers, otherwise single line
      if (allAnswers.length > 1) {
        const bulletPoints = allAnswers.map(ans => `  - ${ans}`).join('\n');
        return `**${q.header}:**\n${bulletPoints}`;
      } else {
        return `**${q.header}:** ${allAnswers[0]}`;
      }
    });

    const answerMessage = `My answers:\n\n${answerLines.join('\n\n')}`;

    if (!sessionId) {
      setValidationError('Session ID not available. Cannot submit answers.');
      return;
    }

    setIsSubmitting(true);

    await sendMessage({
      instanceId: sessionId,
      content: answerMessage,
      onUserMessageSent: () => {
        setIsSubmitting(false);
      },
      onError: (error) => {
        console.error('Failed to send answer:', error);
        setValidationError('Failed to send answer. Please try again.');
        setIsSubmitting(false);
      },
    });
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
    <CollapsibleWidget header={header} toolArgs={toolArgs} result={result} defaultExpanded={true}>
      <div className="p-4 space-y-4">
        {/* Tabs for multiple questions */}
        {questions.length > 1 && !hasAnswered && (
          <div className="flex gap-1 border-b border-gray-200">
            {questions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => setActiveTab(idx)}
                className={`px-4 py-2 type-body-sm font-medium transition-colors border-b-2 ${
                  activeTab === idx
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {q.header}
              </button>
            ))}
          </div>
        )}

        {/* Current question */}
        {questions.map((q, qIdx) => {
          // Show all questions if answered, or only active tab if not answered
          const shouldShow = hasAnswered || (questions.length === 1) || (qIdx === activeTab);
          if (!shouldShow) return null;

          return (
            <div key={qIdx} className="space-y-3">
              <div className="flex items-baseline gap-2 mb-1">
                <div className="type-body font-medium text-gray-900">{q.question}</div>
                {q.multiSelect && (
                  <span className="type-caption text-gray-500 whitespace-nowrap">(Select all that apply)</span>
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
          );
        })}

        {/* Validation error display */}
        {validationError && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 type-body-sm text-red-700">
            {validationError}
          </div>
        )}

        {/* Submit button - show only for latest unanswered question */}
        {!hasAnswered && questions.length > 0 && isLatestMessage && (
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
