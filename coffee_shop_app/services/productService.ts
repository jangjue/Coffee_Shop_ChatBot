import { fireBaseDB } from '../config/firebaseConfig';
import { Product } from '../types/types';
import { ref, get } from 'firebase/database';

const productsRef = ref(fireBaseDB, 'products');

const fetchProducts = async (): Promise<Product[]> => {
  const snapshot = await get(productsRef);
  const data = snapshot.val();
  
  const products: Product[] = [];
  if (data) {
    for (const key in data) {
      if (data.hasOwnProperty(key)) {
        products.push({ ...data[key] });
      }
    }
  }
  
  return products;
};

// Menu items mapping for the chatbot to use
const getMenuItems = async (): Promise<Record<string, number>> => {
  const products = await fetchProducts();
  
  // Create a mapping of item name to price
  const menuItems: Record<string, number> = {};
  products.forEach(product => {
    if (product.name && product.price) {
      menuItems[product.name] = product.price;
    }
  });
  
  return menuItems;
};

// Create a singleton instance of menu items to avoid multiple fetches
let cachedMenuItems: Record<string, number> | null = null;
const getCachedMenuItems = async (): Promise<Record<string, number>> => {
  if (!cachedMenuItems) {
    cachedMenuItems = await getMenuItems();
  }
  return cachedMenuItems;
};

// Function to reset cache if menu is updated
const resetMenuCache = () => {
  cachedMenuItems = null;
};

export { fetchProducts, getMenuItems, getCachedMenuItems, resetMenuCache };