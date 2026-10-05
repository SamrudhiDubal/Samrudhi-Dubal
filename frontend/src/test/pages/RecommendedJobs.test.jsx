import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import RecommendedJobs from '../../pages/RecommendedJobs';
import api from '../../api/axios';

vi.mock('../../api/axios', () => ({ default: { get: vi.fn() } }));

const recommendation = {
  job: { _id: 'j1', title: 'Frontend Developer', company: 'Acme', location: 'Chennai' },
  match: { matchScore: 82, matchedSkills: ['react.js', 'css'], missingSkills: ['typescript'] },
  alreadyApplied: true,
};

function renderPage() {
  return render(
    <MemoryRouter>
      <RecommendedJobs />
    </MemoryRouter>
  );
}

describe('RecommendedJobs page', () => {
  it('lists recommended jobs with match score and skill gaps', async () => {
    api.get.mockResolvedValue({ data: { basedOn: 'resume', recommendations: [recommendation] } });
    renderPage();

    expect(await screen.findByText('Frontend Developer')).toBeInTheDocument();
    expect(screen.getByText('82% AI Match')).toBeInTheDocument();
    expect(screen.getByText('typescript')).toBeInTheDocument();
    expect(screen.getByText('Applied')).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/jobs/recommended');
  });

  it('prompts for a resume upload when matching on profile only', async () => {
    api.get.mockResolvedValue({ data: { basedOn: 'profile', recommendations: [] } });
    renderPage();

    expect(await screen.findByText(/upload a resume/i)).toBeInTheDocument();
    expect(screen.getByText(/no open jobs to recommend/i)).toBeInTheDocument();
  });
});
