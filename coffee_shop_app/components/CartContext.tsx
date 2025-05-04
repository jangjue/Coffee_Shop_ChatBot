import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Alert } from 'react-native';

// Define the type for the cart items
type CartItems = {
  [key: string]: number;  // key is the product ID, value is the quantity
};

interface CartContextType {
  cartItems: CartItems;
  addToCart: (itemKey: string, quantity: number) => void;
  SetQuantityCart: (itemKey: string, delta: number) => void;
  emptyCart: () => void;
  hasItemsInCart: () => boolean;
}

// Create a Cart Context
const CartContext = createContext<CartContextType | undefined>(undefined);

// Create a provider component
export const CartProvider = ({ children }: { children: ReactNode }) => {
  const [cartItems, setCartItems] = useState<CartItems>({});

  const SetQuantityCart = (itemKey: string, delta: number) => {
    setCartItems((prevItems) => ({
      ...prevItems,
      [itemKey]: Math.max((prevItems[itemKey] || 0) + delta, 0),
    }));
  };
  
  const hasItemsInCart = () => {
    return Object.values(cartItems).some(quantity => quantity > 0);
  };

  const addToCart = (itemKey: string, quantity: number) => {
    // Always add to the existing cart without confirmation dialog
    setCartItems((prevItems) => ({
      ...prevItems,
      [itemKey]: (prevItems[itemKey] || 0) + quantity,
    }));
  };
  
  // Keep emptyCart for backward compatibility
  const emptyCart = () => {
    setCartItems({});
  };

  return (
    <CartContext.Provider value={{ 
      cartItems, 
      addToCart,
      emptyCart, 
      SetQuantityCart,
      hasItemsInCart
    }}>
      {children}
    </CartContext.Provider>
  );
};

// Custom hook for using cart context
export const useCart = (): CartContextType => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};