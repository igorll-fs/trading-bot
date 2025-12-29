import { useCallback, useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Skeleton } from '@/components/ui/skeleton';
import { notify } from '@/lib/notify';
import { Save, Key, MessageSquare, Settings as SettingsIcon } from 'lucide-react';
import { apiClient } from '@/lib/api';

const isMaskedValue = (value) => typeof value === 'string' && /(\*\*\*|\.\.\.|\u2022{3,})/.test(value);

const createSchema = ({
  allowBinanceKeyBlank = false,
  allowBinanceSecretBlank = false,
  allowTelegramTokenBlank = false,
} = {}) =>
  z
    .object({
      binance_api_key: z.string().trim(),
      binance_api_secret: z.string().trim(),
      binance_testnet: z.boolean(),
      telegram_bot_token: z.string().trim(),
      telegram_chat_id: z.string().trim().min(1, 'Informe o Chat ID'),
      max_positions: z
        .coerce
        .number({ invalid_type_error: 'Informe um número válido' })
        .refine((value) => !Number.isNaN(value), 'Informe um número válido')
        .pipe(
          z
            .number()
            .min(1, 'Mínimo de 1 posição')
            .max(10, 'Máximo de 10 posições')
            .refine((value) => Number.isInteger(value), 'Informe um número inteiro')
        ),
      risk_percentage: z
        .coerce
        .number({ invalid_type_error: 'Informe um percentual válido' })
        .refine((value) => !Number.isNaN(value), 'Informe um percentual válido')
        .pipe(
          z
            .number()
            .min(0.1, 'Mínimo de 0.1%')
            .max(10, 'Máximo de 10%')
        ),

      selector_min_quote_volume: z
        .coerce
        .number({ invalid_type_error: 'Informe um volume válido' })
        .refine((value) => !Number.isNaN(value), 'Informe um volume válido')
        .pipe(
          z
            .number()
            .min(0, 'Mínimo 0')
        ),

      selector_max_spread_percent: z
        .coerce
        .number({ invalid_type_error: 'Informe um spread válido' })
        .refine((value) => !Number.isNaN(value), 'Informe um spread válido')
        .pipe(
          z
            .number()
            .min(0.01, 'Mínimo 0.01%')
            .max(5, 'Máximo 5%')
        ),

      strategy_min_signal_strength: z
        .coerce
        .number({ invalid_type_error: 'Informe uma força de sinal válida' })
        .refine((value) => !Number.isNaN(value), 'Informe uma força de sinal válida')
        .pipe(
          z
            .number()
            .min(0, 'Mínimo 0')
            .max(100, 'Máximo 100')
            .refine((value) => Number.isInteger(value), 'Use um número inteiro')
        ),

      daily_drawdown_limit_pct: z
        .coerce
        .number({ invalid_type_error: 'Informe um percentual válido' })
        .refine((value) => !Number.isNaN(value), 'Informe um percentual válido')
        .pipe(
          z
            .number()
            .min(0, 'Mínimo 0%')
            .max(100, 'Máximo 100%')
        ),
    })
    .superRefine((data, ctx) => {
      if (!allowBinanceKeyBlank && !data.binance_api_key) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['binance_api_key'], message: 'Informe a API Key completa' });
      }
      if (data.binance_api_key && data.binance_api_key.length < 10) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['binance_api_key'], message: 'A API Key deve ter pelo menos 10 caracteres' });
      }

      if (!allowBinanceSecretBlank && !data.binance_api_secret) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['binance_api_secret'], message: 'Informe o API Secret completo' });
      }
      if (data.binance_api_secret && data.binance_api_secret.length < 10) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['binance_api_secret'], message: 'O Secret deve ter pelo menos 10 caracteres' });
      }

      if (!allowTelegramTokenBlank && !data.telegram_bot_token) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['telegram_bot_token'], message: 'Informe o Token completo do Telegram' });
      }
      if (data.telegram_bot_token && data.telegram_bot_token.length < 20) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['telegram_bot_token'], message: 'Token do Telegram muito curto' });
      }
    });

const SettingsSkeleton = () => (
  <div className="p-8 space-y-6 animate-fade-in">
    <div className="space-y-2">
      <Skeleton className="h-9 w-48" />
      <Skeleton className="h-4 w-64" />
    </div>
    {[1, 2, 3].map((section) => (
      <Card key={section} className="hover-lift">
        <CardHeader className="space-y-2">
          <Skeleton className="h-5 w-52" />
          <Skeleton className="h-3 w-72" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[...Array(3)].map((_, idx) => (
            <div key={idx} className="space-y-2">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-10 w-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    ))}
  </div>
);

const Settings = () => {
  const [loading, setLoading] = useState(true);
  const [previousTestnetState, setPreviousTestnetState] = useState(true);
  const [storedCredentials, setStoredCredentials] = useState({
    binance_api_key: '',
    binance_api_secret: '',
    telegram_bot_token: '',
  });

  const schemaOptions = useMemo(
    () => ({
      allowBinanceKeyBlank: Boolean(storedCredentials.binance_api_key) && !isMaskedValue(storedCredentials.binance_api_key),
      allowBinanceSecretBlank: Boolean(storedCredentials.binance_api_secret) && !isMaskedValue(storedCredentials.binance_api_secret),
      allowTelegramTokenBlank: Boolean(storedCredentials.telegram_bot_token) && !isMaskedValue(storedCredentials.telegram_bot_token),
    }),
    [storedCredentials]
  );

  const schema = useMemo(() => createSchema(schemaOptions), [schemaOptions]);

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      binance_api_key: '',
      binance_api_secret: '',
      binance_testnet: true,
      telegram_bot_token: '',
      telegram_chat_id: '',
      max_positions: 3,
      risk_percentage: 2,
      selector_min_quote_volume: 50000,
      selector_max_spread_percent: 0.25,
      strategy_min_signal_strength: 60,
      daily_drawdown_limit_pct: 0,
    },
  });

  const { control, handleSubmit, reset, watch, setValue, clearErrors, setError, formState } = form;
  const isSubmitting = formState.isSubmitting;

  const binanceTestnet = watch('binance_testnet');
  const binanceApiKeyValue = watch('binance_api_key');
  const binanceApiSecretValue = watch('binance_api_secret');
  const telegramTokenValue = watch('telegram_bot_token');
  const telegramChatIdValue = watch('telegram_chat_id');

  const fetchConfig = useCallback(
    async ({ silent = false } = {}) => {
      if (!silent) {
        setLoading(true);
      }
      try {
        const response = await apiClient.get('/config', { skipGlobalErrorHandler: true });
        const payload = response.data ?? {};
        const normalized = {
          binance_api_key: payload.binance_api_key ?? '',
          binance_api_secret: payload.binance_api_secret ?? '',
          binance_testnet: Boolean(payload.binance_testnet ?? true),
          telegram_bot_token: payload.telegram_bot_token ?? '',
          telegram_chat_id: payload.telegram_chat_id ? String(payload.telegram_chat_id) : '',
          max_positions: typeof payload.max_positions === 'number'
            ? payload.max_positions
            : Number(payload.max_positions) || 3,
          risk_percentage: typeof payload.risk_percentage === 'number'
            ? payload.risk_percentage
            : Number(payload.risk_percentage) || 2,
          selector_min_quote_volume: typeof payload.selector_min_quote_volume === 'number'
            ? payload.selector_min_quote_volume
            : Number(payload.selector_min_quote_volume) || 50000,
          selector_max_spread_percent: typeof payload.selector_max_spread_percent === 'number'
            ? payload.selector_max_spread_percent
            : Number(payload.selector_max_spread_percent) || 0.25,
          strategy_min_signal_strength: typeof payload.strategy_min_signal_strength === 'number'
            ? payload.strategy_min_signal_strength
            : Number(payload.strategy_min_signal_strength) || 60,
          daily_drawdown_limit_pct: typeof payload.daily_drawdown_limit_pct === 'number'
            ? payload.daily_drawdown_limit_pct
            : Number(payload.daily_drawdown_limit_pct) || 0,
        };

        setStoredCredentials({
          binance_api_key: normalized.binance_api_key,
          binance_api_secret: normalized.binance_api_secret,
          telegram_bot_token: normalized.telegram_bot_token,
        });

        setPreviousTestnetState(normalized.binance_testnet);

        reset({
          binance_api_key: normalized.binance_api_key,
          binance_api_secret: normalized.binance_api_secret,
          binance_testnet: normalized.binance_testnet,
          telegram_bot_token: normalized.telegram_bot_token,
          telegram_chat_id: normalized.telegram_chat_id,
          max_positions: normalized.max_positions,
          risk_percentage: normalized.risk_percentage,
          selector_min_quote_volume: normalized.selector_min_quote_volume,
          selector_max_spread_percent: normalized.selector_max_spread_percent,
          strategy_min_signal_strength: normalized.strategy_min_signal_strength,
          daily_drawdown_limit_pct: normalized.daily_drawdown_limit_pct,
        });
      } catch (error) {
        if (error?.isNetworkError) {
          notify.error('Servidor inacessível. Verifique se o backend está em execução.');
        } else {
          const detail = error?.response?.data?.detail;
          notify.error('Erro ao carregar configurações: ' + (detail || error?.message));
        }
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [reset]
  );

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleTestnetChange = useCallback(
    (checked) => {
      if (!checked && previousTestnetState) {
        notify.warning('Atenção: modo real ativado. Cole as API Keys da Binance principal.');
      }
      if (checked && !previousTestnetState) {
        notify.info('Modo testnet ativado. Cole as API Keys de teste.');
      }

      setValue('binance_api_key', '', { shouldDirty: true });
      setValue('binance_api_secret', '', { shouldDirty: true });
      setStoredCredentials((prev) => ({
        ...prev,
        binance_api_key: '',
        binance_api_secret: '',
      }));
      clearErrors(['binance_api_key', 'binance_api_secret']);
    },
    [clearErrors, previousTestnetState, setValue]
  );

  const hasMaskedBinanceKey = isMaskedValue(storedCredentials.binance_api_key);
  const hasMaskedBinanceSecret = isMaskedValue(storedCredentials.binance_api_secret);
  const hasMaskedTelegramToken = isMaskedValue(storedCredentials.telegram_bot_token);

  const isConfigComplete = useMemo(() => {
    const keyFilled = Boolean(binanceApiKeyValue.trim()) || schemaOptions.allowBinanceKeyBlank;
    const secretFilled = Boolean(binanceApiSecretValue.trim()) || schemaOptions.allowBinanceSecretBlank;
    const tokenFilled = Boolean(telegramTokenValue.trim()) || schemaOptions.allowTelegramTokenBlank;
    const chatIdFilled = Boolean(telegramChatIdValue.trim());
    return keyFilled && secretFilled && tokenFilled && chatIdFilled;
  }, [
    binanceApiKeyValue,
    binanceApiSecretValue,
    telegramTokenValue,
    telegramChatIdValue,
    schemaOptions,
  ]);

  const resolveSensitiveValue = useCallback(
    (inputValue, storedValue, allowStoredValue) => {
      const trimmedInput = inputValue.trim();
      if (trimmedInput) {
        return trimmedInput;
      }
      if (allowStoredValue && storedValue && !isMaskedValue(storedValue)) {
        return storedValue;
      }
      return '';
    },
    []
  );

  const onSubmit = useCallback(
    async (values) => {
      clearErrors(['binance_api_key', 'binance_api_secret', 'telegram_bot_token']);

      const resolvedBinanceKey = resolveSensitiveValue(
        values.binance_api_key,
        storedCredentials.binance_api_key,
        schemaOptions.allowBinanceKeyBlank
      );
      const resolvedBinanceSecret = resolveSensitiveValue(
        values.binance_api_secret,
        storedCredentials.binance_api_secret,
        schemaOptions.allowBinanceSecretBlank
      );
      const resolvedTelegramToken = resolveSensitiveValue(
        values.telegram_bot_token,
        storedCredentials.telegram_bot_token,
        schemaOptions.allowTelegramTokenBlank
      );

      let hasError = false;
      if (!resolvedBinanceKey) {
        setError('binance_api_key', { type: 'manual', message: 'Informe a API Key completa' });
        hasError = true;
      }
      if (!resolvedBinanceSecret) {
        setError('binance_api_secret', { type: 'manual', message: 'Informe o API Secret completo' });
        hasError = true;
      }
      if (!resolvedTelegramToken) {
        setError('telegram_bot_token', { type: 'manual', message: 'Informe o Token completo do Telegram' });
        hasError = true;
      }
      if (hasError) {
        return;
      }

      const payload = {
        ...values,
        binance_api_key: resolvedBinanceKey,
        binance_api_secret: resolvedBinanceSecret,
        telegram_bot_token: resolvedTelegramToken,
        telegram_chat_id: values.telegram_chat_id.trim(),
        max_positions: Number(values.max_positions),
        risk_percentage: Number(values.risk_percentage),
        leverage: 1,
        selector_min_quote_volume: Number(values.selector_min_quote_volume),
        selector_max_spread_percent: Number(values.selector_max_spread_percent),
        strategy_min_signal_strength: Number(values.strategy_min_signal_strength),
        daily_drawdown_limit_pct: Number(values.daily_drawdown_limit_pct),
      };

      try {
        await apiClient.post('/config', payload, { skipGlobalErrorHandler: true });
        notify.success('Configurações salvas com sucesso.');
        setPreviousTestnetState(payload.binance_testnet);
        await fetchConfig({ silent: true });
      } catch (error) {
        if (error?.isNetworkError) {
          notify.error('Servidor inacessível ao salvar. Verifique se o backend está em execução.');
        } else if (error?.response) {
          notify.error(
            'Erro ao salvar configurações: ' + (error.response.data.detail || JSON.stringify(error.response.data))
          );
        } else {
          notify.error('Erro ao salvar configurações: ' + (error?.message || String(error)));
        }
      }
    },
    [
      clearErrors,
      fetchConfig,
      resolveSensitiveValue,
      schemaOptions.allowBinanceKeyBlank,
      schemaOptions.allowBinanceSecretBlank,
      schemaOptions.allowTelegramTokenBlank,
      setError,
      storedCredentials,
    ]
  );

  if (loading) {
    return <SettingsSkeleton />;
  }

  return (
    <div className="p-4 sm:p-8 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold gradient-text">Configurações</h1>
        <p className="text-white/50 mt-1">Configure as APIs e parâmetros do bot</p>
      </div>

      <Form {...form}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 stagger-children">
          <Card data-testid="binance-config-card" className="glass-card hover:shadow-glow-violet transition-all duration-300">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 shadow-lg shadow-violet-500/30">
                  <Key size={18} className="text-white" />
                </div>
                <span className="text-white">API Binance Spot</span>
              </CardTitle>
              <CardDescription className="text-white/50">Configure suas credenciais da Binance Spot API</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <FormField
                control={control}
                name="binance_testnet"
                render={({ field }) => (
                  <div
                    className={`p-4 rounded-lg border-2 transition-all ${
                      field.value
                        ? 'bg-green-50 dark:bg-green-950/30 border-green-500'
                        : 'bg-red-50 dark:bg-red-950/30 border-red-500'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <Switch
                        id="testnet"
                        data-testid="binance-testnet-switch"
                        checked={field.value}
                        onCheckedChange={(checked) => {
                          field.onChange(checked);
                          handleTestnetChange(checked);
                        }}
                        className="mt-1"
                      />
                      <div className="flex-1 space-y-2">
                        <Label htmlFor="testnet" className="cursor-pointer font-semibold text-base">
                          {field.value ? 'Modo Testnet ativado' : 'Modo Mainnet ativado'}
                        </Label>
                        <p
                          className={`text-sm font-medium ${
                            field.value ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'
                          }`}
                        >
                          {field.value
                            ? 'Operando com fundos virtuais. Ideal para testar sem riscos.'
                            : 'Operando com fundos reais. Revise suas chaves antes de continuar.'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              />

              <div className="space-y-4">
                <FormField
                  control={control}
                  name="binance_api_key"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-2">
                        API Key *
                        {binanceTestnet ? (
                          <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
                            Testnet
                          </span>
                        ) : (
                          <span className="text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 px-2 py-0.5 rounded">
                            Mainnet
                          </span>
                        )}
                      </FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          type="text"
                          value={field.value ?? ''}
                          placeholder={
                            hasMaskedBinanceKey
                              ? 'API Key configurada. Cole a chave completa para atualizar.'
                              : binanceTestnet
                                ? 'Cole sua API Key do testnet.'
                                : 'Cole sua API Key da Binance.'
                          }
                          className={
                            binanceTestnet
                              ? 'border-green-300 focus-visible:border-green-500 focus-visible:ring-green-500'
                              : 'border-red-300 focus-visible:border-red-500 focus-visible:ring-red-500'
                          }
                        />
                      </FormControl>
                      {hasMaskedBinanceKey && !field.value && (
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                          API Key já cadastrada. Cole uma nova para substituir.
                        </p>
                      )}
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={control}
                  name="binance_api_secret"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-2">
                        API Secret *
                        {binanceTestnet ? (
                          <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
                            Testnet
                          </span>
                        ) : (
                          <span className="text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 px-2 py-0.5 rounded">
                            Mainnet
                          </span>
                        )}
                      </FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          type="password"
                          value={field.value ?? ''}
                          placeholder={
                            hasMaskedBinanceSecret
                              ? 'API Secret configurado. Cole o valor completo para atualizar.'
                              : binanceTestnet
                                ? 'Cole seu Secret do testnet.'
                                : 'Cole seu Secret da Binance.'
                          }
                          className={
                            binanceTestnet
                              ? 'border-green-300 focus-visible:border-green-500 focus-visible:ring-green-500'
                              : 'border-red-300 focus-visible:border-red-500 focus-visible:ring-red-500'
                          }
                        />
                      </FormControl>
                      {hasMaskedBinanceSecret && !field.value && (
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                          API Secret já cadastrado. Cole um novo para substituir.
                        </p>
                      )}
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div
                className={`p-3 rounded-lg border ${
                  binanceTestnet
                    ? 'bg-green-50/50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
                    : 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800'
                }`}
              >
                <p className="text-sm font-semibold mb-2">
                  {binanceTestnet ? 'Como obter credenciais do testnet:' : 'Como obter credenciais da Binance:'}
                </p>
                {binanceTestnet ? (
                  <div className="space-y-1 text-sm text-green-700 dark:text-green-400">
                    <p>Acesse https://testnet.binance.vision e faça login.</p>
                    <p>Abra Dashboard &gt; API Keys e gere uma Spot Testnet API Key.</p>
                    <p>Copie a API Key e o Secret e cole acima.</p>
                  </div>
                ) : (
                  <div className="space-y-1 text-sm text-amber-700 dark:text-amber-400">
                    <p>Acesse https://www.binance.com/en/my/settings/api-management.</p>
                    <p>Crie uma nova chave apenas com permissão Spot &amp; Margin Trading.</p>
                    <p>Recomenda-se configurar restrições de IP antes de ativar.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card data-testid="telegram-config-card" className="glass-card hover:shadow-glow-cyan transition-all duration-300">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 shadow-lg shadow-cyan-500/30">
                  <MessageSquare size={18} className="text-white" />
                </div>
                <span className="text-white">Notificações Telegram</span>
              </CardTitle>
              <CardDescription className="text-white/50">Receba alertas de execução diretamente no Telegram</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={control}
                name="telegram_bot_token"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Bot Token *</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        type="text"
                        value={field.value ?? ''}
                        placeholder={
                          hasMaskedTelegramToken
                            ? 'Token configurado. Cole o valor completo para atualizar.'
                            : 'Exemplo: 123456:ABC-DEF1234567890'
                        }
                      />
                    </FormControl>
                    {hasMaskedTelegramToken && !field.value && (
                      <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                        Token já cadastrado. Cole um novo para substituir.
                      </p>
                    )}
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={control}
                name="telegram_chat_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Chat ID *</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        type="text"
                        value={field.value ?? ''}
                        placeholder="Exemplo: 123456789"
                        onChange={(event) => {
                          const sanitized = event.target.value.replace(/[^0-9-]/g, '');
                          field.onChange(sanitized);
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <p className="text-xs text-muted-foreground">
                Crie seu bot com o @BotFather e recupere o Chat ID com o @userinfobot.
              </p>
            </CardContent>
          </Card>

          <Card data-testid="risk-config-card" className="glass-card hover:shadow-glow-emerald transition-all duration-300">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg shadow-emerald-500/30">
                  <SettingsIcon size={18} className="text-white" />
                </div>
                <span className="text-white">Gestão de risco</span>
              </CardTitle>
              <CardDescription className="text-white/50">Defina os limites de exposição por operação</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={control}
                name="max_positions"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Máximo de posições simultâneas</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        type="number"
                        min={1}
                        max={10}
                        value={field.value ?? ''}
                        onChange={(event) => field.onChange(event.target.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={control}
                name="risk_percentage"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Risco por trade (%)</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        type="number"
                        step="0.1"
                        min={0.1}
                        max={10}
                        value={field.value ?? ''}
                        onChange={(event) => field.onChange(event.target.value)}
                      />
                    </FormControl>
                    <FormDescription>
                      Percentual do saldo arriscado por trade. Recomendado entre 1% e 3%.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={control}
                name="daily_drawdown_limit_pct"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Perda máxima diária (%)</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        type="number"
                        step="0.1"
                        min={0}
                        max={100}
                        value={field.value ?? ''}
                        onChange={(event) => field.onChange(event.target.value)}
                      />
                    </FormControl>
                    <FormDescription>
                      Ao atingir o limite, o bot pausa novas entradas. Ex.: 1.5 para travar o dia.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="space-y-1 text-sm">
                <p className="font-semibold">Modo Spot</p>
                <p className="text-muted-foreground">
                  As operações utilizam alavancagem fixa de 1x. O tamanho da posição depende do percentual de risco configurado.
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="flex items-center justify-end gap-3">
            {!isConfigComplete && (
              <p className="text-sm text-white/40">
                Preencha os campos obrigatórios para habilitar o salvamento.
              </p>
            )}
            <Button
              type="submit"
              disabled={isSubmitting || !isConfigComplete}
              data-testid="settings-save-button"
              className={`
                h-12 px-6 rounded-xl font-medium gap-2
                transition-all duration-300 ease-out
                ${isConfigComplete && !isSubmitting
                  ? 'bg-gradient-to-r from-violet-500 to-cyan-500 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 hover:scale-[1.02]'
                  : 'bg-white/10 text-white/50'
                }
              `}
            >
              <Save size={18} className={isSubmitting ? 'animate-spin' : ''} />
              {isSubmitting ? 'Salvando...' : 'Salvar configurações'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
};

export default Settings;
