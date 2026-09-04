const mongoose = require('mongoose');

const jobSchema = new mongoose.Schema(
  {
    title: { type: String, required: true, trim: true },
    description: { type: String, required: true },
    company: { type: String, required: true, trim: true },
    location: { type: String, trim: true, default: 'Remote' },
    jobType: {
      type: String,
      enum: ['full-time', 'part-time', 'contract', 'internship'],
      default: 'full-time',
    },
    experienceLevel: {
      type: String,
      enum: ['entry', 'mid', 'senior', 'lead'],
      default: 'entry',
    },
    salaryMin: { type: Number },
    salaryMax: { type: Number },
    skillsRequired: [{ type: String, trim: true, lowercase: true }],
    employer: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    status: { type: String, enum: ['open', 'closed'], default: 'open' },
    applicationsCount: { type: Number, default: 0 },
  },
  { timestamps: true }
);

jobSchema.index({ title: 'text', description: 'text', company: 'text' });

module.exports = mongoose.model('Job', jobSchema);
