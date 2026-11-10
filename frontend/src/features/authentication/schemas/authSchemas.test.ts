import { describe, it, expect } from 'vitest';
import { registerSchema, loginSchema } from './authSchemas';

describe('authSchemas', () => {
  describe('loginSchema', () => {
    it('should validate valid email and password', () => {
      const result = loginSchema.safeParse({
        email: 'user@example.com',
        password: 'Password123!',
      });
      expect(result.success).toBe(true);
    });

    it('should fail on invalid email format', () => {
      const result = loginSchema.safeParse({
        email: 'not-an-email',
        password: 'Password123!',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe('Please enter a valid email address');
      }
    });

    it('should fail on empty password', () => {
      const result = loginSchema.safeParse({
        email: 'user@example.com',
        password: '',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe('Password is required');
      }
    });
  });

  describe('registerSchema', () => {
    it('should validate matching passwords and valid fields', () => {
      const result = registerSchema.safeParse({
        full_name: 'John Doe',
        email: 'john@example.com',
        password: 'StrongPassword123!',
        password_confirmation: 'StrongPassword123!',
      });
      expect(result.success).toBe(true);
    });

    it('should fail when passwords do not match', () => {
      const result = registerSchema.safeParse({
        full_name: 'John Doe',
        email: 'john@example.com',
        password: 'StrongPassword123!',
        password_confirmation: 'DifferentPassword123!',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe('Passwords do not match');
      }
    });

    it('should fail when password is shorter than 8 characters', () => {
      const result = registerSchema.safeParse({
        full_name: 'John Doe',
        email: 'john@example.com',
        password: 'short',
        password_confirmation: 'short',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe('Password must be at least 8 characters');
      }
    });

    it('should fail when full_name is too short', () => {
      const result = registerSchema.safeParse({
        full_name: 'J',
        email: 'john@example.com',
        password: 'StrongPassword123!',
        password_confirmation: 'StrongPassword123!',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe('Full name must be at least 2 characters');
      }
    });
  });
});

