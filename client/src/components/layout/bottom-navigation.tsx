import { useLocation } from 'wouter';
import { Home, Compass, FileText, DollarSign, Users } from 'lucide-react';

export function BottomNavigation() {
  const [location, setLocation] = useLocation();

  const isActive = (path: string) => {
    return location === path;
  };

  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/explore', label: 'Explore', icon: Compass },
    { path: '/claim', label: 'Claim', icon: FileText },
    { path: '/payment', label: 'Pay', icon: DollarSign },
    { path: '/chama', label: 'Chama', icon: Users },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white shadow-lg border-t border-neutral-200 z-10">
      <div className="container mx-auto px-4">
        <div className="flex justify-around">
          {navItems.map((item) => (
            <button
              key={item.path}
              onClick={() => setLocation(item.path)}
              className={`py-3 flex flex-col items-center ${
                isActive(item.path) ? 'text-primary' : 'text-neutral-500'
              }`}
            >
              <item.icon size={20} />
              <span className="text-xs mt-1">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}
