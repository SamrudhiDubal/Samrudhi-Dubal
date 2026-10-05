jest.mock('../../models/User');

const jwt = require('jsonwebtoken');
const User = require('../../models/User');
const { protect, authorize } = require('../../middleware/auth');

describe('auth middleware', () => {
  const OLD_ENV = process.env;

  beforeEach(() => {
    jest.resetAllMocks();
    process.env = { ...OLD_ENV, JWT_SECRET: 'test-secret' };
  });

  afterAll(() => {
    process.env = OLD_ENV;
  });

  function mockRes() {
    return { status: jest.fn().mockReturnThis(), json: jest.fn() };
  }

  describe('protect', () => {
    it('rejects requests with no Authorization header', async () => {
      const req = { headers: {} };
      const res = mockRes();
      const next = jest.fn();

      await protect(req, res, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(next).not.toHaveBeenCalled();
    });

    it('rejects an invalid token', async () => {
      const req = { headers: { authorization: 'Bearer not-a-real-token' } };
      const res = mockRes();
      const next = jest.fn();

      await protect(req, res, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(next).not.toHaveBeenCalled();
    });

    it('attaches req.user and calls next for a valid token and active user', async () => {
      const fakeUser = { _id: 'user1', isActive: true, role: 'candidate' };
      User.findById.mockResolvedValue(fakeUser);
      const token = jwt.sign({ id: 'user1' }, 'test-secret');
      const req = { headers: { authorization: `Bearer ${token}` } };
      const res = mockRes();
      const next = jest.fn();

      await protect(req, res, next);

      expect(req.user).toBe(fakeUser);
      expect(next).toHaveBeenCalled();
    });

    it('rejects a deactivated user with 403', async () => {
      User.findById.mockResolvedValue({ _id: 'user1', isActive: false });
      const token = jwt.sign({ id: 'user1' }, 'test-secret');
      const req = { headers: { authorization: `Bearer ${token}` } };
      const res = mockRes();
      const next = jest.fn();

      await protect(req, res, next);

      expect(res.status).toHaveBeenCalledWith(403);
      expect(next).not.toHaveBeenCalled();
    });

    it('rejects when the user no longer exists', async () => {
      User.findById.mockResolvedValue(null);
      const token = jwt.sign({ id: 'ghost' }, 'test-secret');
      const req = { headers: { authorization: `Bearer ${token}` } };
      const res = mockRes();
      const next = jest.fn();

      await protect(req, res, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(next).not.toHaveBeenCalled();
    });
  });

  describe('authorize', () => {
    it('calls next when the user role is allowed', () => {
      const req = { user: { role: 'employer' } };
      const res = mockRes();
      const next = jest.fn();

      authorize('employer', 'admin')(req, res, next);

      expect(next).toHaveBeenCalled();
    });

    it('returns 403 when the user role is not allowed', () => {
      const req = { user: { role: 'candidate' } };
      const res = mockRes();
      const next = jest.fn();

      authorize('employer', 'admin')(req, res, next);

      expect(res.status).toHaveBeenCalledWith(403);
      expect(next).not.toHaveBeenCalled();
    });
  });
});
