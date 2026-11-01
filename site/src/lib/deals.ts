import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Reads the latest verified deals from the local JSON data file.
 * @returns {Array} Array of deal objects
 */
export function getVerifiedDeals() {
    try {
        // Resolve relative to this file's directory (site/src/lib/)
        const filePath = path.resolve(__dirname, '../../data/deals.json');
        const data = fs.readFileSync(filePath, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error("Error reading deals.json:", error);
        return [];
    }
}
