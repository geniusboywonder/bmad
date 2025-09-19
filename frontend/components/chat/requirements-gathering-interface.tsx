"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

type Question = {
  id: string;
  text: string;
};

interface RequirementsGatheringInterfaceProps {
  questions: Question[];
  onSubmit: (answers: Record<string, string>) => void;
}

export function RequirementsGatheringInterface({
  questions,
  onSubmit,
}: RequirementsGatheringInterfaceProps) {
  const [answers, setAnswers] = React.useState<Record<string, string>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(answers);
  };

  const handleAnswerChange = (id: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  };

  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Please Answer These Questions</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {questions.map((q) => (
              <div key={q.id} className="space-y-2">
                <Label htmlFor={q.id}>{q.text}</Label>
                <Input
                  id={q.id}
                  value={answers[q.id] || ""}
                  onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                  placeholder="Your answer..."
                  required
                />
              </div>
            ))}
            <div className="flex justify-end">
              <Button type="submit">Submit Answers</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
