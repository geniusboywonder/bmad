/**
 * Project Creation Form
 * Form component for creating new projects with backend integration
 */

"use client";

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Plus, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useProjectStore } from '@/lib/stores/project-store';
import { useToast } from '@/hooks/use-toast';

// Validation schema for project creation
const projectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(100, 'Name must be less than 100 characters'),
  description: z.string().optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  budget_limit: z.number().min(0, 'Budget must be positive').max(10000, 'Budget limit exceeded').optional(),
  estimated_duration: z.number().min(1, 'Duration must be at least 1 hour').max(720, 'Maximum 720 hours').optional(),
  tags: z.array(z.string()).default([]),
  agent_config: z.object({
    max_agents: z.number().min(1).max(10).default(3),
    agent_types: z.array(z.string()).default(['analyst', 'architect', 'developer']),
  }).optional(),
});

type ProjectFormData = z.infer<typeof projectSchema>;

interface ProjectCreationFormProps {
  onSuccess?: (project: any) => void;
  trigger?: React.ReactNode;
}

export function ProjectCreationForm({ onSuccess, trigger }: ProjectCreationFormProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const { createProject, isLoading, error, clearError } = useProjectStore();
  const { toast } = useToast();

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
    setValue,
    watch,
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      priority: 'medium',
      budget_limit: 100,
      estimated_duration: 24,
      tags: [],
      agent_config: {
        max_agents: 3,
        agent_types: ['analyst', 'architect', 'developer'],
      },
    },
  });

  const watchedPriority = watch('priority');

  const onSubmit = async (data: ProjectFormData) => {
    clearError();

    try {
      const projectData = {
        ...data,
        tags,
        status: 'pending' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      const newProject = await createProject(projectData);

      if (newProject) {
        toast({
          title: 'Project Created',
          description: `Project "${newProject.name}" has been created successfully.`,
          duration: 5000,
        });

        setIsOpen(false);
        reset();
        setTags([]);
        onSuccess?.(newProject);
      }
    } catch (error) {
      console.error('Project creation error:', error);
      toast({
        title: 'Creation Failed',
        description: 'Failed to create project. Please try again.',
        variant: 'destructive',
        duration: 5000,
      });
    }
  };

  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      const updatedTags = [...tags, newTag.trim()];
      setTags(updatedTags);
      setValue('tags', updatedTags);
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    const updatedTags = tags.filter(tag => tag !== tagToRemove);
    setTags(updatedTags);
    setValue('tags', updatedTags);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'default';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button className="bg-primary hover:bg-primary/90">
            <Plus className="w-4 h-4 mr-2" />
            Create Project
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Set up a new project with agent orchestration and HITL safety controls.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Error Display */}
          {error && (
            <div className="flex items-center space-x-2 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <AlertCircle className="w-4 h-4 text-destructive" />
              <span className="text-sm text-destructive">
                {typeof error === 'string' ? error : error?.message || 'An error occurred'}
              </span>
            </div>
          )}

          {/* Basic Information */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Project Name *</Label>
                <Input
                  id="name"
                  placeholder="Enter project name"
                  {...register('name')}
                  className={errors.name ? 'border-destructive' : ''}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe your project goals and requirements"
                  rows={3}
                  {...register('description')}
                />
                {errors.description && (
                  <p className="text-sm text-destructive">{errors.description.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="priority">Priority</Label>
                  <Select value={watchedPriority} onValueChange={(value) => setValue('priority', value as any)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                  </Select>
                  <Badge variant={getPriorityColor(watchedPriority)} className="text-xs">
                    {watchedPriority?.toUpperCase()} PRIORITY
                  </Badge>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="estimated_duration">Estimated Duration (hours)</Label>
                  <Input
                    id="estimated_duration"
                    type="number"
                    min="1"
                    max="720"
                    placeholder="24"
                    {...register('estimated_duration', { valueAsNumber: true })}
                  />
                  {errors.estimated_duration && (
                    <p className="text-sm text-destructive">{errors.estimated_duration.message}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Budget Configuration */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Budget & Safety</CardTitle>
              <CardDescription>Configure budget limits and safety controls</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="budget_limit">Budget Limit ($)</Label>
                <Input
                  id="budget_limit"
                  type="number"
                  min="0"
                  max="10000"
                  step="0.01"
                  placeholder="100.00"
                  {...register('budget_limit', { valueAsNumber: true })}
                />
                {errors.budget_limit && (
                  <p className="text-sm text-destructive">{errors.budget_limit.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Emergency stop will be triggered if this limit is exceeded
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Tags */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Tags</CardTitle>
              <CardDescription>Add tags to organize and categorize your project</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Input
                  placeholder="Add a tag"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                />
                <Button type="button" variant="outline" onClick={addTag}>
                  Add
                </Button>
              </div>

              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <Badge
                      key={tag}
                      variant="secondary"
                      className="cursor-pointer"
                      onClick={() => removeTag(tag)}
                    >
                      {tag} ×
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isValid || isLoading}
              className="min-w-[120px]"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Create Project
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}