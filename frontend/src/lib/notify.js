import { toast } from '@/components/ui/sonner';

const baseOptions = {
  duration: 3500,
  closeButton: true,
};

const mergeOptions = (options) => ({
  ...baseOptions,
  ...options,
});

const notify = {
  success(message, options) {
    return toast.success(message, mergeOptions(options));
  },
  error(message, options) {
    return toast.error(message, mergeOptions(options));
  },
  warning(message, options) {
    return toast.warning(message, mergeOptions(options));
  },
  info(message, options) {
    return toast.info(message, mergeOptions(options));
  },
  promise(promise, { loading, success, error, ...options }) {
    return toast.promise(promise, {
      loading,
      success,
      error,
      ...mergeOptions(options),
    });
  },
  custom: toast,
};

export { notify };
