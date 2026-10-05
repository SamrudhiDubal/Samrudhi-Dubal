import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import JobCard from '../../components/JobCard';

const job = {
  _id: 'job1',
  title: 'Backend Engineer',
  company: 'Acme Corp',
  location: 'Remote',
  jobType: 'full-time',
  skillsRequired: ['node.js', 'mongodb', 'express', 'rest', 'docker', 'aws', 'kubernetes'],
};

function renderJobCard(props = {}) {
  return render(
    <MemoryRouter>
      <JobCard job={{ ...job, ...props }} />
    </MemoryRouter>
  );
}

describe('JobCard', () => {
  it('renders the job title, company and location', () => {
    renderJobCard();
    expect(screen.getByText('Backend Engineer')).toBeInTheDocument();
    expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    expect(screen.getByText('Remote')).toBeInTheDocument();
  });

  it('links to the job detail page', () => {
    renderJobCard();
    expect(screen.getByRole('link')).toHaveAttribute('href', '/jobs/job1');
  });

  it('renders the job type with hyphens replaced by spaces', () => {
    renderJobCard();
    expect(screen.getByText('full time')).toBeInTheDocument();
  });

  it('shows at most the first 6 required skills', () => {
    renderJobCard();
    expect(screen.getByText('node.js')).toBeInTheDocument();
    expect(screen.getByText('aws')).toBeInTheDocument();
    expect(screen.queryByText('kubernetes')).not.toBeInTheDocument();
  });
});
