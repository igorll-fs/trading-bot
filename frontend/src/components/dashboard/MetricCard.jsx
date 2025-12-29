import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const MetricCard = ({
  title,
  value,
  valueNode,
  description,
  icon: Icon,
  valueClassName = '',
  iconClassName = '',
  children,
}) => {
  return (
    <Card className="hover-lift">
      <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          {Icon ? <Icon size={18} className={iconClassName} /> : null}
          {title}
        </CardTitle>
        {description ? <span className="text-xs text-muted-foreground">{description}</span> : null}
      </CardHeader>
      <CardContent className="space-y-2">
        <div className={`text-3xl font-bold ${valueClassName}`}>
          {valueNode ?? value}
        </div>
        {children}
      </CardContent>
    </Card>
  );
};

export { MetricCard };
