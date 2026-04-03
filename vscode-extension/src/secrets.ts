import * as vscode from 'vscode';

export type SecretKeyName =
  | 'GROQ_API_KEY'
  | 'LANGSMITH_API_KEY'
  | 'OLLAMA_CLOUD_API_KEY'
  | 'OPENROUTER_API_KEY'
  | 'TAVILY_API_KEY';

type SecretDefinition = {
  id: SecretKeyName;
  label: string;
  provider?: string;
  requiredForScanning: boolean;
};

const SECRET_DEFINITIONS: SecretDefinition[] = [
  { id: 'OPENROUTER_API_KEY', label: 'OpenRouter API key', provider: 'openrouter', requiredForScanning: true },
  { id: 'GROQ_API_KEY', label: 'Groq API key', provider: 'groq', requiredForScanning: true },
  { id: 'OLLAMA_CLOUD_API_KEY', label: 'Ollama Cloud API key', provider: 'ollama_cloud', requiredForScanning: true },
  { id: 'TAVILY_API_KEY', label: 'Tavily API key', requiredForScanning: false },
  { id: 'LANGSMITH_API_KEY', label: 'LangSmith API key', requiredForScanning: false }
];

const SECRET_BY_ID = new Map<SecretKeyName, SecretDefinition>(
  SECRET_DEFINITIONS.map(definition => [definition.id, definition])
);

const SECRET_BY_PROVIDER = new Map<string, SecretDefinition>(
  SECRET_DEFINITIONS.filter(definition => definition.provider).map(definition => [definition.provider as string, definition])
);

function normalizeSecret(value: string | undefined | null): string | undefined {
  const trimmed = String(value ?? '').trim();
  return trimmed || undefined;
}

export function providerDisplayName(provider: string): string {
  return (
    {
      openrouter: 'OpenRouter',
      groq: 'Groq',
      ollama_cloud: 'Ollama Cloud',
      ollama_local: 'Ollama Local'
    }[provider] ?? provider
  );
}

export function requiredSecretNameForProvider(provider: string): SecretKeyName | undefined {
  return SECRET_BY_PROVIDER.get(provider)?.id;
}

export class SecretManager {
  constructor(
    private readonly secrets: vscode.SecretStorage,
    private readonly output: vscode.OutputChannel
  ) {}

  async buildProcessEnv(): Promise<NodeJS.ProcessEnv> {
    const overrides: NodeJS.ProcessEnv = {};
    for (const definition of SECRET_DEFINITIONS) {
      const value = await this.getStoredSecret(definition.id);
      if (value) {
        overrides[definition.id] = value;
      }
    }
    return overrides;
  }

  async hasCredentialForProvider(provider: string): Promise<boolean> {
    const secretName = requiredSecretNameForProvider(provider);
    if (!secretName) {
      return true;
    }
    return Boolean(await this.resolveSecretValue(secretName));
  }

  async ensureProviderCredential(
    provider: string,
    options: { interactive?: boolean; reason?: 'activation' | 'scan' | 'setup' } = {}
  ): Promise<boolean> {
    const secretName = requiredSecretNameForProvider(provider);
    if (!secretName) {
      return true;
    }

    const existing = await this.resolveSecretValue(secretName);
    if (existing) {
      return true;
    }

    if (!options.interactive) {
      return false;
    }

    const definition = SECRET_BY_ID.get(secretName);
    if (!definition) {
      return false;
    }

    const action = await vscode.window.showWarningMessage(
      `AI Ethics needs your own ${definition.label} before it can scan with ${providerDisplayName(provider)}.`,
      'Set API Key',
      'Open Setup',
      'Cancel'
    );

    if (action === 'Set API Key') {
      return this.promptToStoreSecret(secretName);
    }

    if (action === 'Open Setup') {
      const changed = await this.openSetup(provider);
      return changed ? this.hasCredentialForProvider(provider) : false;
    }

    return false;
  }

  async promptToStoreSecret(secretName?: SecretKeyName): Promise<boolean> {
    const definition = secretName ? SECRET_BY_ID.get(secretName) : await this.pickSecretDefinition();
    if (!definition) {
      return false;
    }

    const value = await vscode.window.showInputBox({
      title: `Set ${definition.label}`,
      prompt: `Enter your own ${definition.label}. It will be stored in VS Code SecretStorage on this machine only.`,
      password: true,
      ignoreFocusOut: true,
      validateInput: input => (normalizeSecret(input) ? undefined : `${definition.label} cannot be empty.`)
    });

    if (value === undefined) {
      return false;
    }

    await this.secrets.store(definition.id, value.trim());
    this.output.appendLine(`Stored ${definition.label} in VS Code SecretStorage.`);
    return true;
  }

  async removeSecret(): Promise<boolean> {
    const definition = await this.pickSecretDefinition('Select the stored secret to remove.');
    if (!definition) {
      return false;
    }

    const existing = await this.getStoredSecret(definition.id);
    if (!existing) {
      void vscode.window.showInformationMessage(`No stored ${definition.label} was found in VS Code SecretStorage.`);
      return false;
    }

    await this.secrets.delete(definition.id);
    this.output.appendLine(`Removed ${definition.label} from VS Code SecretStorage.`);
    return true;
  }

  async openSetup(preferredProvider?: string): Promise<boolean> {
    const preferredSecret = preferredProvider ? requiredSecretNameForProvider(preferredProvider) : undefined;
    const choice = await vscode.window.showQuickPick(
      [
        {
          label: preferredSecret ? `Set ${providerDisplayName(preferredProvider as string)} API key` : 'Set provider API key',
          target: 'set-provider' as const
        },
        {
          label: 'Set optional API key',
          target: 'set-optional' as const
        },
        {
          label: 'Remove stored API key',
          target: 'remove' as const
        },
        {
          label: 'Open AI Ethics settings',
          target: 'settings' as const
        }
      ],
      {
        title: 'AI Ethics Setup',
        placeHolder: 'Choose a setup action.'
      }
    );

    if (!choice) {
      return false;
    }

    if (choice.target === 'set-provider') {
      return this.promptToStoreSecret(preferredSecret);
    }

    if (choice.target === 'set-optional') {
      const optional = await this.pickSecretDefinition(
        'Select the optional secret to configure.',
        definition => !definition.requiredForScanning
      );
      return optional ? this.promptToStoreSecret(optional.id) : false;
    }

    if (choice.target === 'remove') {
      return this.removeSecret();
    }

    await vscode.commands.executeCommand('workbench.action.openSettings', 'aiEthics');
    return false;
  }

  private async pickSecretDefinition(
    title = 'Select the secret to configure.',
    predicate: (definition: SecretDefinition) => boolean = () => true
  ): Promise<SecretDefinition | undefined> {
    const items = SECRET_DEFINITIONS.filter(predicate).map(definition => ({
      label: definition.label,
      description: definition.provider ? `Used for ${providerDisplayName(definition.provider)} scans` : 'Optional integration',
      definition
    }));

    const selected = await vscode.window.showQuickPick(items, {
      title,
      placeHolder: 'Choose a secret.'
    });

    return selected?.definition;
  }

  private async getStoredSecret(secretName: SecretKeyName): Promise<string | undefined> {
    return normalizeSecret(await this.secrets.get(secretName));
  }

  private async resolveSecretValue(secretName: SecretKeyName): Promise<string | undefined> {
    const stored = await this.getStoredSecret(secretName);
    if (stored) {
      return stored;
    }
    return normalizeSecret(process.env[secretName]);
  }
}
