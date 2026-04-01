import type {TypographyBreakStrategy} from './typographySystems';
import type {ScaleRole} from './typeScale';

type BreakOptions = {
	maxChars: number;
	role: ScaleRole;
	maxWordsPerBlock: number;
};

const CONNECTORS = new Set([
	'a',
	'an',
	'and',
	'as',
	'at',
	'da',
	'de',
	'do',
	'dos',
	'e',
	'em',
	'for',
	'in',
	'na',
	'no',
	'of',
	'on',
	'or',
	'para',
	'the',
	'to',
]);

const isConnector = (word: string): boolean => CONNECTORS.has(word.toLowerCase());
const endsPhrase = (word: string): boolean => /[,:;.!?]$/.test(word);

const preferredWordsPerLine = (role: ScaleRole, maxWordsPerBlock: number): number => {
	if (role === 'display') {
		return Math.min(4, Math.max(2, maxWordsPerBlock));
	}
	if (role === 'title') {
		return Math.min(5, Math.max(3, maxWordsPerBlock));
	}
	if (role === 'caption') {
		return Math.min(4, Math.max(2, maxWordsPerBlock));
	}
	return Math.min(10, Math.max(4, maxWordsPerBlock));
};

const rebalanceTrailingSingleton = (lines: string[]): string[] => {
	if (lines.length < 2) {
		return lines;
	}

	const lastWords = lines[lines.length - 1].trim().split(/\s+/);
	if (lastWords.length !== 1) {
		return lines;
	}

	const previousWords = lines[lines.length - 2].trim().split(/\s+/);
	if (previousWords.length <= 2) {
		return lines;
	}

	lastWords.unshift(previousWords.pop() ?? '');
	lines[lines.length - 2] = previousWords.join(' ');
	lines[lines.length - 1] = lastWords.join(' ');
	return lines.filter(Boolean);
};

const breakSemantic = (words: string[], options: BreakOptions): string[] => {
	const lines: string[] = [];
	const preferred = preferredWordsPerLine(options.role, options.maxWordsPerBlock);
	let current: string[] = [];

	for (let index = 0; index < words.length; index += 1) {
		const word = words[index];
		const next = words[index + 1] ?? '';
		const tentative = [...current, word];
		const tentativeText = tentative.join(' ');
		const currentFull =
			current.length >= preferred ||
			tentativeText.length > options.maxChars ||
			current.length >= options.maxWordsPerBlock;

		const shouldCommit =
			current.length >= 2 &&
			(endsPhrase(current[current.length - 1]) ||
				(currentFull && !isConnector(word) && !isConnector(next)));

		if (shouldCommit) {
			lines.push(current.join(' '));
			current = [word];
			continue;
		}

		if (tentativeText.length > options.maxChars && current.length >= 2) {
			lines.push(current.join(' '));
			current = [word];
			continue;
		}

		current = tentative;
	}

	if (current.length > 0) {
		lines.push(current.join(' '));
	}

	return rebalanceTrailingSingleton(lines);
};

const breakBalanced = (words: string[], options: BreakOptions): string[] => {
	const lines: string[] = [];
	const totalChars = words.join(' ').length;
	const targetLines = Math.max(
		1,
		Math.ceil(totalChars / Math.max(options.maxChars - 4, Math.floor(options.maxChars * 0.75))),
	);
	const idealChars = Math.max(8, Math.ceil(totalChars / targetLines));
	let current: string[] = [];

	for (const word of words) {
		const tentative = [...current, word];
		const tentativeText = tentative.join(' ');
		const shouldWrap =
			current.length >= 2 &&
			(tentativeText.length > options.maxChars ||
				(tentativeText.length >= idealChars && !isConnector(word)));

		if (shouldWrap) {
			lines.push(current.join(' '));
			current = [word];
			continue;
		}

		current = tentative;
	}

	if (current.length > 0) {
		lines.push(current.join(' '));
	}

	return rebalanceTrailingSingleton(lines);
};

export const breakText = (
	content: string,
	strategy: TypographyBreakStrategy,
	options: BreakOptions,
): string => {
	const normalized = content.replace(/\s+/g, ' ').trim();
	if (!normalized || strategy === 'none') {
		return content;
	}

	const words = normalized.split(' ');
	if (words.length <= 2) {
		return normalized;
	}

	const lines =
		strategy === 'balanced'
			? breakBalanced(words, options)
			: breakSemantic(words, options);

	return lines.join('\n');
};
