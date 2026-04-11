import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './main.scss';
import App from './components/App/App.jsx';
import { store, persistor } from './store/store.js';
import { PersistGate } from 'redux-persist/integration/react';
import { Provider } from 'react-redux';

createRoot(document.getElementById('root')).render(
   <StrictMode>
      <Provider store={store}>
         <PersistGate loading={null} persistor={persistor}>
            <App />
         </PersistGate>
      </Provider>
   </StrictMode>
);
